import datetime

import httpx
import pytest

from api.clients import pncp as pncp_module
from api.clients.pncp import PNCPClient, PNCPRateLimitError

UMA_DATA = datetime.date(2026, 1, 1)
OUTRA_DATA = datetime.date(2026, 1, 2)


@pytest.fixture(autouse=True)
def sem_sleep_de_verdade(monkeypatch):
    monkeypatch.setattr(pncp_module.time, "sleep", lambda segundos: None)


def _pagina(dados, pagina=1, total_paginas=1):
    return httpx.Response(200, json={"data": dados, "totalPaginas": total_paginas, "numeroPagina": pagina})


def test_retry_apos_rate_limit_429():
    chamadas = {"n": 0}

    def handler(request):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            return httpx.Response(429, text="rate limited")
        return _pagina([{"id": 1}])

    client = PNCPClient(transport=httpx.MockTransport(handler), min_interval=0)
    resultado = client.buscar_contratacoes_publicadas(UMA_DATA, OUTRA_DATA, codigo_modalidade=6)

    assert chamadas["n"] == 2
    assert resultado["data"] == [{"id": 1}]


def test_retry_apos_timeout_de_rede():
    chamadas = {"n": 0}

    def handler(request):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            raise httpx.ReadTimeout("timeout simulado", request=request)
        return _pagina([])

    client = PNCPClient(transport=httpx.MockTransport(handler), min_interval=0)
    resultado = client.buscar_contratacoes_publicadas(UMA_DATA, OUTRA_DATA, codigo_modalidade=6)

    assert chamadas["n"] == 2
    assert resultado["data"] == []


def test_204_vira_pagina_vazia_sem_quebrar_o_json():
    client = PNCPClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(204)), min_interval=0
    )
    resultado = client.buscar_contratacoes_publicadas(UMA_DATA, OUTRA_DATA, codigo_modalidade=2)

    assert resultado == {"data": [], "totalPaginas": 0}


def test_esgota_tentativas_de_rate_limit_e_levanta_erro_especifico():
    client = PNCPClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(429, text="rate limited")),
        min_interval=0,
    )
    with pytest.raises(PNCPRateLimitError):
        client.buscar_contratacoes_publicadas(UMA_DATA, OUTRA_DATA, codigo_modalidade=6, max_tentativas=1)


def test_erro_5xx_persistente_propaga_http_status_error():
    client = PNCPClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(500, text="erro interno")),
        min_interval=0,
    )
    with pytest.raises(httpx.HTTPStatusError):
        client.buscar_contratacoes_publicadas(UMA_DATA, OUTRA_DATA, codigo_modalidade=6, max_tentativas=1)


def test_buscar_todas_paginas_percorre_ate_o_fim():
    respostas = [
        _pagina([{"id": 1}], pagina=1, total_paginas=2),
        _pagina([{"id": 2}], pagina=2, total_paginas=2),
    ]

    def handler(request):
        return respostas.pop(0)

    client = PNCPClient(transport=httpx.MockTransport(handler), min_interval=0)
    itens = list(client.buscar_todas_paginas(UMA_DATA, OUTRA_DATA, codigo_modalidade=6))

    assert itens == [{"id": 1}, {"id": 2}]


def test_buscar_todas_paginas_respeita_max_paginas():
    def handler(request):
        return _pagina([{"id": 1}], pagina=1, total_paginas=5)

    client = PNCPClient(transport=httpx.MockTransport(handler), min_interval=0)
    itens = list(
        client.buscar_todas_paginas(UMA_DATA, OUTRA_DATA, codigo_modalidade=6, max_paginas=1)
    )

    assert itens == [{"id": 1}]
