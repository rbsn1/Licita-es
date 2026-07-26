import datetime
import re
import statistics
from collections.abc import Iterable

from webapp.clients.painel_precos import PainelPrecosClient
from webapp.clients.pncp import PNCPClient, parse_numero_controle

_STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "em", "com",
    "para", "por", "no", "na", "nos", "nas", "um", "uma", "uns", "umas",
    "ao", "aos", "à", "às", "que", "se", "ou", "sob", "sobre",
}


def _palavras_significativas(texto: str) -> set[str]:
    palavras = re.findall(r"[a-zà-ÿ]+", texto.lower())
    return {p for p in palavras if len(p) > 3 and p not in _STOPWORDS}


# RF-PRE-01: filtra, do histórico de contratos do órgão, os que têm objeto
# textualmente semelhante ao objeto do edital em análise — aproximação por
# sobreposição de palavras significativas, na ausência de um código CATMAT/CATSER
# já extraído do edital (ver item em aberto em requisitos-precificacao.md)
def filtrar_contratos_por_objeto(
    contratos: Iterable[dict], objeto_edital: str, sobreposicao_minima: float = 0.3
) -> list[dict]:
    palavras_edital = _palavras_significativas(objeto_edital)
    if not palavras_edital:
        return []

    compativeis = []
    for contrato in contratos:
        palavras_contrato = _palavras_significativas(contrato.get("objetoContrato", ""))
        if not palavras_contrato:
            continue
        sobreposicao = len(palavras_edital & palavras_contrato) / len(palavras_edital)
        if sobreposicao >= sobreposicao_minima:
            compativeis.append(contrato)
    return compativeis


# RF-PRE-01/RF-PRE-04: calcula a faixa de preço (mínimo/ideal/máximo) a partir dos
# valores totais de referência (histórico de contratos do PNCP — mesma unidade do
# orçamento estimado do edital). O máximo nunca ultrapassa o orçamento estimado do
# órgão, quando conhecido, já que propostas acima do valor estimado costumam ser
# desclassificadas. Sinaliza "não confiável" quando a amostra é pequena demais
# (RF-PRE-04) — nesse caso a faixa cai para um desconto padrão sobre o orçamento
# estimado, só para não deixar o cliente sem nenhuma referência.
def calcular_faixa_preco(
    valor_estimado: float | None,
    valores_referencia: list[float],
    amostra_minima: int = 3,
) -> dict:
    amostra = sorted(v for v in valores_referencia if v and v > 0)
    confiavel = len(amostra) >= amostra_minima

    if not confiavel:
        if valor_estimado is None:
            return {"minimo": None, "ideal": None, "maximo": None, "confiavel": False, "amostra": len(amostra)}
        return {
            "minimo": round(valor_estimado * 0.9, 2),
            "ideal": round(valor_estimado * 0.97, 2),
            "maximo": round(valor_estimado, 2),
            "confiavel": False,
            "amostra": len(amostra),
        }

    minimo = amostra[0]
    ideal = statistics.median(amostra)
    maximo = amostra[-1]
    if valor_estimado is not None:
        maximo = min(maximo, valor_estimado)
        ideal = min(ideal, maximo)
        minimo = min(minimo, ideal)

    return {
        "minimo": round(minimo, 2),
        "ideal": round(ideal, 2),
        "maximo": round(maximo, 2),
        "confiavel": True,
        "amostra": len(amostra),
    }


# RF-PRE-01: preço unitário de referência do Painel de Preços — sinal complementar,
# reportado separado da faixa de valor total (unidades diferentes, ver
# PainelPrecosClient.buscar_precos_unitarios)
def preco_unitario_referencia(precos_unitarios: list[float]) -> dict | None:
    amostra = sorted(v for v in precos_unitarios if v and v > 0)
    if not amostra:
        return None
    return {"mediana": round(statistics.median(amostra), 2), "amostra": len(amostra)}


class PrecificacaoAgent:
    def __init__(
        self, pncp_client: PNCPClient, painel_client: PainelPrecosClient | None = None
    ) -> None:
        self._pncp = pncp_client
        self._painel = painel_client

    # RF-PRE-01/RF-PRE-02: pipeline completo — busca o histórico de contratos do
    # mesmo órgão do edital, filtra por semelhança de objeto e calcula a faixa de
    # preço. `codigo_item_catalogo` é opcional: só quando informado (hoje não é
    # extraído pela Análise/triagem, ver item em aberto na spec) o Painel de
    # Preços entra como sinal complementar de preço unitário.
    def calcular_para_edital(
        self,
        edital: dict,
        codigo_item_catalogo: int | None = None,
        janela_dias: int = 730,
        max_paginas_contratos: int | None = None,
    ) -> dict:
        cnpj_orgao, _ano, _sequencial = parse_numero_controle(edital["pncp_id"])
        hoje = datetime.date.today()
        data_inicial = hoje - datetime.timedelta(days=janela_dias)

        contratos = list(
            self._pncp.buscar_todos_contratos(
                cnpj_orgao, data_inicial, hoje, max_paginas=max_paginas_contratos
            )
        )
        compativeis = filtrar_contratos_por_objeto(contratos, edital["objeto"])
        valores_referencia = [
            valor
            for contrato in compativeis
            if (valor := contrato.get("valorGlobal") or contrato.get("valorInicial")) is not None
        ]

        resultado = calcular_faixa_preco(edital.get("valor_estimado"), valores_referencia)

        preco_unitario_painel = None
        if self._painel is not None and codigo_item_catalogo is not None:
            precos_unitarios = self._painel.buscar_precos_unitarios(
                codigo_item_catalogo,
                data_compra_inicio=data_inicial,
                data_compra_fim=hoje,
            )
            preco_unitario_painel = preco_unitario_referencia(precos_unitarios)
        resultado["preco_unitario_painel_precos"] = preco_unitario_painel

        return resultado
