import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from data.db import get_session
from data.formatacao import formatar_valor_brl
from data.models import Cliente, Edital, Esfera, FaixaPreco, Match, ResumoEdital

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.filters["valor_brl"] = formatar_valor_brl


# recebidos como string e validados manualmente (em vez de tipar o parâmetro do
# FastAPI direto como Esfera/date) porque o form do dashboard submete "" pros
# campos deixados em branco — o parsing automático do FastAPI rejeita "" como
# data/enum inválidos e devolve 422 em vez de tratar como "sem filtro"
def _esfera_valida(valor: str | None) -> Esfera | None:
    if not valor:
        return None
    try:
        return Esfera(valor)
    except ValueError:
        return None


def _data_valida(valor: str | None) -> datetime.date | None:
    if not valor:
        return None
    try:
        return datetime.date.fromisoformat(valor)
    except ValueError:
        return None


# RF-04/RF-AUTH-01: dashboard consultável, agora protegido por sessão de login
# (substitui o link mágico por token), filtrável por score, órgão, esfera,
# modalidade e data
@router.get("/dashboard")
def dashboard(
    request: Request,
    score_minimo: float = Query(0.0),
    uf: str | None = Query(None),
    esfera: str | None = Query(None),
    modalidade: str | None = Query(None),
    data_inicial: str | None = Query(None),
    data_final: str | None = Query(None),
    session: Session = Depends(get_session),
):
    cliente_id = request.session.get("cliente_id")
    if cliente_id is None:
        return RedirectResponse(url="/login", status_code=303)

    cliente = session.query(Cliente).filter_by(id=cliente_id).one_or_none()
    if cliente is None:
        request.session.pop("cliente_id", None)
        return RedirectResponse(url="/login", status_code=303)

    esfera_filtro = _esfera_valida(esfera)
    data_inicial_filtro = _data_valida(data_inicial)
    data_final_filtro = _data_valida(data_final)

    # RF-ANL-03/RF-PRE-03: resumo e faixa de preço são opcionais (outerjoin) —
    # nem todo edital com match já foi processado pelo pipeline de análise/precificação
    consulta = (
        session.query(Match, Edital, ResumoEdital, FaixaPreco)
        .join(Edital, Match.edital_id == Edital.id)
        .outerjoin(ResumoEdital, ResumoEdital.edital_id == Edital.id)
        .outerjoin(FaixaPreco, FaixaPreco.edital_id == Edital.id)
        .filter(Match.cliente_id == cliente.id, Match.score >= score_minimo)
    )
    if uf:
        consulta = consulta.filter(Edital.uf == uf.upper())
    if esfera_filtro:
        consulta = consulta.filter(Edital.esfera == esfera_filtro)
    if modalidade:
        consulta = consulta.filter(Edital.modalidade == modalidade)
    if data_inicial_filtro:
        consulta = consulta.filter(Edital.data_publicacao >= data_inicial_filtro)
    if data_final_filtro:
        consulta = consulta.filter(Edital.data_publicacao <= data_final_filtro)

    resultados = consulta.order_by(Match.score.desc()).all()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "cliente": cliente,
            "resultados": resultados,
            "total_resultados": len(resultados),
            "melhor_score": resultados[0][0].score if resultados else None,
            "filtros": {
                "score_minimo": score_minimo,
                "uf": uf or "",
                "esfera": esfera_filtro.value if esfera_filtro else "",
                "modalidade": modalidade or "",
                "data_inicial": data_inicial_filtro.isoformat() if data_inicial_filtro else "",
                "data_final": data_final_filtro.isoformat() if data_final_filtro else "",
            },
            "esferas": list(Esfera),
        },
    )
