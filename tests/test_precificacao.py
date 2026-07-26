import httpx
import pytest

from agents.precificacao.agent import (
    PrecificacaoAgent,
    calcular_faixa_preco,
    filtrar_contratos_por_objeto,
    preco_unitario_referencia,
)
from webapp.clients import pncp as pncp_module
from webapp.clients.painel_precos import PainelPrecosClient
from webapp.clients.pncp import PNCPClient


@pytest.fixture(autouse=True)
def sem_sleep_de_verdade(monkeypatch):
    monkeypatch.setattr(pncp_module.time, "sleep", lambda segundos: None)


def _contrato(objeto="Aquisição de material de informática", valor_global=100000.0):
    return {"objetoContrato": objeto, "valorGlobal": valor_global}


def test_filtrar_contratos_por_objeto_mantem_semelhantes():
    contratos = [
        _contrato("Aquisição de material de informática para escritório"),
        _contrato("Contratação de serviço de limpeza predial"),
    ]
    resultado = filtrar_contratos_por_objeto(contratos, "Aquisição de material de informática")
    assert len(resultado) == 1
    assert "informática" in resultado[0]["objetoContrato"]


def test_filtrar_contratos_por_objeto_sem_semelhanca_retorna_vazio():
    contratos = [_contrato("Contratação de serviço de limpeza predial")]
    resultado = filtrar_contratos_por_objeto(contratos, "Aquisição de material de informática")
    assert resultado == []


def test_calcular_faixa_preco_com_amostra_suficiente():
    resultado = calcular_faixa_preco(valor_estimado=150000.0, valores_referencia=[90000, 100000, 110000])
    assert resultado["confiavel"] is True
    assert resultado["amostra"] == 3
    assert resultado["minimo"] == 90000.0
    assert resultado["ideal"] == 100000.0
    assert resultado["maximo"] == 110000.0


def test_calcular_faixa_preco_nunca_ultrapassa_valor_estimado():
    resultado = calcular_faixa_preco(valor_estimado=95000.0, valores_referencia=[90000, 100000, 110000])
    assert resultado["maximo"] == 95000.0
    assert resultado["ideal"] <= 95000.0
    assert resultado["minimo"] <= resultado["ideal"]


def test_calcular_faixa_preco_amostra_insuficiente_usa_desconto_padrao_sobre_estimado():
    resultado = calcular_faixa_preco(valor_estimado=100000.0, valores_referencia=[90000])
    assert resultado["confiavel"] is False
    assert resultado["maximo"] == 100000.0
    assert resultado["minimo"] == 90000.0


def test_calcular_faixa_preco_sem_amostra_e_sem_valor_estimado():
    resultado = calcular_faixa_preco(valor_estimado=None, valores_referencia=[])
    assert resultado == {"minimo": None, "ideal": None, "maximo": None, "confiavel": False, "amostra": 0}


def test_preco_unitario_referencia_calcula_mediana():
    assert preco_unitario_referencia([10.0, 20.0, 30.0]) == {"mediana": 20.0, "amostra": 3}


def test_preco_unitario_referencia_sem_amostra_retorna_none():
    assert preco_unitario_referencia([]) is None


def _edital():
    return {
        "pncp_id": "83102277000152-1-000424/2026",
        "objeto": "Aquisição de material de informática",
        "valor_estimado": 150000.0,
    }


def test_precificacao_agent_pipeline_completo_com_pncp_e_painel():
    def handler_pncp(request):
        if request.url.path.endswith("/v1/contratos"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        _contrato("Aquisição de material de informática", 90000.0),
                        _contrato("Aquisição de material de informática", 110000.0),
                        _contrato("Aquisição de material de informática", 100000.0),
                        _contrato("Serviço de dedetização", 5000.0),
                    ],
                    "totalPaginas": 1,
                },
            )
        raise AssertionError(f"chamada inesperada: {request.url}")

    def handler_painel(request):
        return httpx.Response(
            200,
            json={
                "resultado": [{"precoUnitario": 100.0}, {"precoUnitario": 120.0}],
                "totalPaginas": 1,
            },
        )

    pncp = PNCPClient(transport=httpx.MockTransport(handler_pncp), min_interval=0)
    painel = PainelPrecosClient(transport=httpx.MockTransport(handler_painel))
    agent = PrecificacaoAgent(pncp, painel)

    resultado = agent.calcular_para_edital(_edital(), codigo_item_catalogo=12345)

    assert resultado["confiavel"] is True
    assert resultado["amostra"] == 3
    assert resultado["maximo"] == 110000.0
    assert resultado["preco_unitario_painel_precos"] == {"mediana": 110.0, "amostra": 2}


def test_precificacao_agent_sem_codigo_catalogo_nao_consulta_painel():
    def handler_pncp(request):
        return httpx.Response(200, json={"data": [], "totalPaginas": 1})

    def handler_painel(request):
        raise AssertionError("não deveria consultar o Painel de Preços sem codigo_item_catalogo")

    pncp = PNCPClient(transport=httpx.MockTransport(handler_pncp), min_interval=0)
    painel = PainelPrecosClient(transport=httpx.MockTransport(handler_painel))
    agent = PrecificacaoAgent(pncp, painel)

    resultado = agent.calcular_para_edital(_edital())

    assert resultado["preco_unitario_painel_precos"] is None
