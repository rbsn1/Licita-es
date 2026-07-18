import httpx
import pytest

from webapp.clients.pncp import (
    PNCPClient,
    parse_numero_controle,
    selecionar_documento_edital,
)


def test_parse_numero_controle():
    assert parse_numero_controle("83102277000152-1-000424/2026") == ("83102277000152", 2026, 424)


def test_parse_numero_controle_formato_invalido():
    with pytest.raises(ValueError):
        parse_numero_controle("formato-qualquer")


def test_selecionar_documento_edital_encontra_por_titulo():
    arquivos = [
        {"titulo": "ETP", "tipoDocumentoNome": "Edital", "url": "https://x/1"},
        {"titulo": "EDITAL", "tipoDocumentoNome": "Edital", "url": "https://x/2"},
        {"titulo": "PLANILHA", "tipoDocumentoNome": "Outros Documentos", "url": "https://x/3"},
    ]
    documento = selecionar_documento_edital(arquivos)
    assert documento is not None
    assert documento["url"] == "https://x/2"


def test_selecionar_documento_edital_sem_correspondencia():
    arquivos = [{"titulo": "PLANILHA", "tipoDocumentoNome": "Outros Documentos", "url": "https://x/3"}]
    assert selecionar_documento_edital(arquivos) is None


def test_buscar_arquivos_compra_monta_url_correta():
    capturada = {}

    def handler(request):
        capturada["url"] = str(request.url)
        return httpx.Response(200, json=[{"titulo": "EDITAL", "url": "https://x/2"}])

    client = PNCPClient(transport=httpx.MockTransport(handler))
    arquivos = client.buscar_arquivos_compra("83102277000152", 2026, 424)

    assert capturada["url"] == (
        "https://pncp.gov.br/api/pncp/v1/orgaos/83102277000152/compras/2026/424/arquivos"
    )
    assert arquivos == [{"titulo": "EDITAL", "url": "https://x/2"}]


def test_baixar_arquivo_retorna_conteudo_bruto():
    client = PNCPClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"%PDF-conteudo"))
    )
    assert client.baixar_arquivo("https://x/2") == b"%PDF-conteudo"
