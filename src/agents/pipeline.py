import datetime
import logging

import anthropic
from sqlalchemy.orm import Session

from agents.analise_edital.agent import analisar_edital_por_numero_controle
from agents.precificacao.agent import PrecificacaoAgent
from data.models import Edital, FaixaPreco, Match, ResumoEdital
from webapp.clients.pncp import PNCPClient

logger = logging.getLogger(__name__)


def _parse_prazo(valor: str | None) -> datetime.datetime | None:
    if not valor:
        return None
    try:
        return datetime.datetime.fromisoformat(valor)
    except ValueError:
        logger.warning("prazo_limite_proposta em formato inesperado: %r", valor)
        return None


# RF-ANL-01/RF-ANL-02: analisa editais com match relevante (score >= limiar de
# alerta, RF-03) que ainda não têm resumo persistido. Idempotente (RNF-01 de
# requisitos-analise-edital.md): um edital já resumido nunca é reanalisado. Falha
# num edital não interrompe os demais (RNF-02).
def analisar_editais_pendentes(
    session: Session,
    pncp: PNCPClient,
    anthropic_client: anthropic.Anthropic,
    score_minimo: float = 40.0,
    limite: int = 20,
) -> int:
    editais_pendentes = (
        session.query(Edital)
        .join(Match, Match.edital_id == Edital.id)
        .outerjoin(ResumoEdital, ResumoEdital.edital_id == Edital.id)
        .filter(Match.score >= score_minimo, ResumoEdital.id.is_(None))
        .distinct()
        .limit(limite)
        .all()
    )

    analisados = 0
    for edital in editais_pendentes:
        try:
            dados = analisar_edital_por_numero_controle(pncp, anthropic_client, edital.pncp_id)
        except Exception:
            logger.exception("falha ao analisar edital %s", edital.pncp_id)
            continue

        session.add(
            ResumoEdital(
                edital_id=edital.id,
                prazo_limite_proposta=_parse_prazo(dados["prazo_limite_proposta"]),
                valor_estimado=dados["valor_estimado"],
                requisitos_habilitacao=dados["requisitos_habilitacao"],
                clausulas_risco=dados["clausulas_risco"],
            )
        )
        session.commit()
        analisados += 1

    return analisados


# RF-PRE-01/RF-PRE-02: precifica editais com match relevante já analisados
# (ResumoEdital existe) que ainda não têm faixa de preço persistida. Roda depois
# de analisar_editais_pendentes no mesmo ciclo, mas também retenta editais cujo
# resumo já existia mas a precificação falhou num ciclo anterior.
def precificar_editais_pendentes(
    session: Session,
    precificacao: PrecificacaoAgent,
    score_minimo: float = 40.0,
    limite: int = 20,
) -> int:
    editais_pendentes = (
        session.query(Edital, ResumoEdital)
        .join(Match, Match.edital_id == Edital.id)
        .join(ResumoEdital, ResumoEdital.edital_id == Edital.id)
        .outerjoin(FaixaPreco, FaixaPreco.edital_id == Edital.id)
        .filter(Match.score >= score_minimo, FaixaPreco.id.is_(None))
        .distinct()
        .limit(limite)
        .all()
    )

    precificados = 0
    for edital, resumo in editais_pendentes:
        valor_referencia = (
            float(resumo.valor_estimado)
            if resumo.valor_estimado is not None
            else edital.valor_estimado
        )
        try:
            resultado = precificacao.calcular_para_edital(
                {"pncp_id": edital.pncp_id, "objeto": edital.objeto, "valor_estimado": valor_referencia}
            )
            session.add(
                FaixaPreco(
                    edital_id=edital.id,
                    minimo=resultado["minimo"],
                    ideal=resultado["ideal"],
                    maximo=resultado["maximo"],
                    confiavel=resultado["confiavel"],
                    amostra=resultado["amostra"],
                )
            )
            session.commit()
            precificados += 1
        except Exception:
            session.rollback()
            logger.exception("falha ao precificar edital %s", edital.pncp_id)

    return precificados


# RF-ANL-02/RF-PRE-02: pipeline completo do ciclo pós-varredura — analisa e, em
# seguida, precifica os editais com match relevante ainda pendentes
def processar_editais_pendentes(
    session: Session,
    pncp: PNCPClient,
    anthropic_client: anthropic.Anthropic,
    precificacao: PrecificacaoAgent,
    score_minimo: float = 40.0,
    limite: int = 20,
) -> dict:
    analisados = analisar_editais_pendentes(
        session, pncp, anthropic_client, score_minimo=score_minimo, limite=limite
    )
    precificados = precificar_editais_pendentes(
        session, precificacao, score_minimo=score_minimo, limite=limite
    )
    return {"analisados": analisados, "precificados": precificados}
