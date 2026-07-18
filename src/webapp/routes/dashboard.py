import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from data.db import get_session
from data.formatacao import formatar_valor_brl
from data.models import Cliente, Edital, Esfera, Match

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
templates.env.filters["valor_brl"] = formatar_valor_brl


# RF-04: dashboard consultável, filtrável por score, órgão, esfera, modalidade e data
@router.get("/dashboard/{token}")
def dashboard(
    token: str,
    request: Request,
    score_minimo: float = Query(0.0),
    uf: str | None = Query(None),
    esfera: Esfera | None = Query(None),
    modalidade: str | None = Query(None),
    data_inicial: datetime.date | None = Query(None),
    data_final: datetime.date | None = Query(None),
    session: Session = Depends(get_session),
):
    cliente = session.query(Cliente).filter_by(access_token=token).one_or_none()
    if cliente is None:
        raise HTTPException(status_code=404, detail="link inválido")

    consulta = (
        session.query(Match, Edital)
        .join(Edital, Match.edital_id == Edital.id)
        .filter(Match.cliente_id == cliente.id, Match.score >= score_minimo)
    )
    if uf:
        consulta = consulta.filter(Edital.uf == uf.upper())
    if esfera:
        consulta = consulta.filter(Edital.esfera == esfera)
    if modalidade:
        consulta = consulta.filter(Edital.modalidade == modalidade)
    if data_inicial:
        consulta = consulta.filter(Edital.data_publicacao >= data_inicial)
    if data_final:
        consulta = consulta.filter(Edital.data_publicacao <= data_final)

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
                "esfera": esfera.value if esfera else "",
                "modalidade": modalidade or "",
                "data_inicial": data_inicial.isoformat() if data_inicial else "",
                "data_final": data_final.isoformat() if data_final else "",
            },
            "esferas": list(Esfera),
        },
    )
