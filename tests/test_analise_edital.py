import json
from types import SimpleNamespace

import httpx

from agents.analise_edital.agent import (
    analisar_edital_por_numero_controle,
    analisar_texto_edital,
)
from webapp.clients.pncp import PNCPClient


class _FakeMessages:
    def __init__(self, resultado: dict):
        self._resultado = resultado
        self.chamadas = []

    def create(self, **kwargs):
        self.chamadas.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=json.dumps(self._resultado))]
        )


class _FakeAnthropicClient:
    def __init__(self, resultado: dict):
        self.messages = _FakeMessages(resultado)


def test_analisar_texto_edital_retorna_resumo_estruturado():
    resultado_esperado = {
        "prazo_limite_proposta": "2026-08-01T09:00:00",
        "valor_estimado": 450000.0,
        "requisitos_habilitacao": ["Certidão negativa de débitos federais"],
        "clausulas_risco": ["Prazo de entrega de 5 dias úteis após a assinatura"],
    }
    client = _FakeAnthropicClient(resultado_esperado)

    resultado = analisar_texto_edital(client, "texto do edital de exemplo")

    assert resultado == resultado_esperado
    assert client.messages.chamadas[0]["model"] == "claude-opus-4-8"


def test_analisar_edital_por_numero_controle_pipeline_completo(monkeypatch):
    resultado_esperado = {
        "prazo_limite_proposta": None,
        "valor_estimado": None,
        "requisitos_habilitacao": [],
        "clausulas_risco": [],
    }

    def handler(request):
        if request.url.path.endswith("/arquivos"):
            return httpx.Response(
                200,
                json=[{"titulo": "EDITAL", "url": "https://pncp.gov.br/pncp-api/v1/x/1"}],
            )
        return httpx.Response(200, content=b"%PDF-fake")

    pncp = PNCPClient(transport=httpx.MockTransport(handler))
    anthropic_client = _FakeAnthropicClient(resultado_esperado)

    monkeypatch.setattr(
        "agents.analise_edital.agent.extrair_texto_pdf", lambda conteudo: "texto extraído"
    )

    resultado = analisar_edital_por_numero_controle(
        pncp, anthropic_client, "83102277000152-1-000424/2026"
    )

    assert resultado == resultado_esperado
