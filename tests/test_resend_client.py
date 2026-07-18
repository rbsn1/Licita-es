import json

import httpx
import pytest

from webapp.clients.resend_client import ResendClient


def test_enviar_email_monta_payload_correto():
    capturado = {}

    def handler(request):
        capturado["json"] = json.loads(request.content)
        capturado["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"id": "abc123"})

    client = ResendClient(
        api_key="chave-teste",
        from_email="remetente@teste.com",
        transport=httpx.MockTransport(handler),
    )
    resultado = client.enviar_email("destino@teste.com", "Assunto teste", "<p>corpo</p>")

    assert resultado == {"id": "abc123"}
    assert capturado["auth"] == "Bearer chave-teste"
    assert capturado["json"] == {
        "from": "remetente@teste.com",
        "to": ["destino@teste.com"],
        "subject": "Assunto teste",
        "html": "<p>corpo</p>",
    }


def test_enviar_email_propaga_erro_http():
    client = ResendClient(
        api_key="chave-teste",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(403, json={"message": "domain not verified"})
        ),
    )
    with pytest.raises(httpx.HTTPStatusError):
        client.enviar_email("destino@teste.com", "assunto", "<p>x</p>")
