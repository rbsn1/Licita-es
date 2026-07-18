import datetime
import logging

import httpx
from sqlalchemy.orm import Session

from webapp.clients.pncp import MODALIDADES_LEI_14133, PNCPClient, PNCPRateLimitError, parse_contratacao
from webapp.clients.resend_client import ResendClient
from data.models import Alerta, CanalAlerta, Cliente, Edital, Match, PerfilCliente, StatusAlerta
from data.settings import settings

logger = logging.getLogger(__name__)

PESOS_CRITERIOS = {
    "palavras_chave": 0.5,
    "uf": 0.3,
    "valor": 0.2,
}


class ProspeccaoAgent:
    def __init__(self, pncp_client: PNCPClient) -> None:
        self._pncp = pncp_client

    def buscar_editais_publicados(
        self,
        data_inicial: datetime.date,
        data_final: datetime.date,
        modalidades: dict[int, str] | None = None,
        max_paginas_por_modalidade: int | None = None,
    ) -> list[dict]:
        modalidades = modalidades if modalidades is not None else MODALIDADES_LEI_14133
        editais_por_pncp_id: dict[str, dict] = {}
        for codigo, nome in modalidades.items():
            try:
                paginas = self._pncp.buscar_todas_paginas(
                    data_inicial,
                    data_final,
                    codigo,
                    max_paginas=max_paginas_por_modalidade,
                )
                for item in paginas:
                    edital = parse_contratacao(item)
                    editais_por_pncp_id[edital["pncp_id"]] = edital
            except (httpx.HTTPError, PNCPRateLimitError) as erro:
                logger.warning("falha ao buscar modalidade %s (%s): %s", codigo, nome, erro)
                continue
        return list(editais_por_pncp_id.values())

    def calcular_score(self, edital: dict, perfil: PerfilCliente) -> float:
        pesos_ativos: dict[str, float] = {}
        pontos: dict[str, float] = {}

        if perfil.palavras_chave:
            pesos_ativos["palavras_chave"] = PESOS_CRITERIOS["palavras_chave"]
            objeto = edital["objeto"].lower()
            acertos = sum(1 for termo in perfil.palavras_chave if termo.lower() in objeto)
            pontos["palavras_chave"] = min(acertos / len(perfil.palavras_chave), 1.0)

        if perfil.ufs:
            pesos_ativos["uf"] = PESOS_CRITERIOS["uf"]
            pontos["uf"] = 1.0 if edital["uf"] in perfil.ufs else 0.0

        if perfil.valor_minimo is not None or perfil.valor_maximo is not None:
            pesos_ativos["valor"] = PESOS_CRITERIOS["valor"]
            valor = edital["valor_estimado"]
            dentro_da_faixa = valor is not None and (
                perfil.valor_minimo is None or valor >= float(perfil.valor_minimo)
            ) and (perfil.valor_maximo is None or valor <= float(perfil.valor_maximo))
            pontos["valor"] = 1.0 if dentro_da_faixa else 0.0

        if not pesos_ativos:
            return 0.0

        peso_total = sum(pesos_ativos.values())
        score = sum(pontos[criterio] * peso for criterio, peso in pesos_ativos.items()) / peso_total
        return round(score * 100, 2)

    def filtrar_compativeis(
        self, editais: list[dict], perfil: PerfilCliente, score_minimo: float = 40.0
    ) -> list[tuple[dict, float]]:
        pontuados = [(edital, self.calcular_score(edital, perfil)) for edital in editais]
        compativeis = [(edital, score) for edital, score in pontuados if score >= score_minimo]
        return sorted(compativeis, key=lambda par: par[1], reverse=True)

    def persistir_resultados(
        self, session: Session, cliente_id: int, resultados: list[tuple[dict, float]]
    ) -> list[Match]:
        matches = []
        for dados_edital, score in resultados:
            edital = (
                session.query(Edital).filter_by(pncp_id=dados_edital["pncp_id"]).one_or_none()
            )
            if edital is None:
                edital = Edital(**dados_edital)
                session.add(edital)
                session.flush()

            match = (
                session.query(Match)
                .filter_by(cliente_id=cliente_id, edital_id=edital.id)
                .one_or_none()
            )
            if match is None:
                match = Match(cliente_id=cliente_id, edital_id=edital.id, score=score)
                session.add(match)
                session.flush()
                session.add(Alerta(match_id=match.id, canal=CanalAlerta.email))
            else:
                match.score = score
            matches.append(match)

        session.commit()
        return matches


def _montar_corpo_email(edital: Edital, score: float, cliente: Cliente) -> str:
    valor = f"R$ {edital.valor_estimado:,.2f}" if edital.valor_estimado else "não informado"
    dashboard_url = f"{settings.dashboard_base_url}/dashboard/{cliente.access_token}"
    return (
        f"<p>Novo edital com {score:.0f}% de aderência ao seu perfil:</p>"
        f"<p><strong>{edital.orgao}</strong> ({edital.uf})</p>"
        f"<p>{edital.objeto}</p>"
        f"<p>Valor estimado: {valor}</p>"
        f'<p><a href="{edital.link_pncp}">Ver edital no PNCP</a></p>'
        f'<p><a href="{dashboard_url}">Ver todos os editais compatíveis no seu painel</a></p>'
    )


def enviar_alertas_pendentes(session: Session, resend_client: ResendClient, limite: int = 50) -> int:
    alertas = (
        session.query(Alerta)
        .filter(Alerta.status == StatusAlerta.pendente, Alerta.canal == CanalAlerta.email)
        .limit(limite)
        .all()
    )

    enviados = 0
    for alerta in alertas:
        match = alerta.match
        try:
            resend_client.enviar_email(
                destinatario=match.cliente.email,
                assunto=f"Novo edital compatível ({match.score:.0f}% de aderência): {match.edital.orgao}",
                corpo_html=_montar_corpo_email(match.edital, match.score, match.cliente),
            )
            alerta.status = StatusAlerta.enviado
            alerta.enviado_em = datetime.datetime.now(datetime.timezone.utc)
            enviados += 1
        except httpx.HTTPError as erro:
            alerta.status = StatusAlerta.falhou
            corpo = erro.response.text if isinstance(erro, httpx.HTTPStatusError) else str(erro)
            logger.warning("falha ao enviar alerta %s para %s: %s", alerta.id, match.cliente.email, corpo)

    session.commit()
    return enviados
