import datetime
import re
import time
from collections.abc import Iterator

import httpx

from data.models import Esfera
from data.settings import settings

_NUMERO_CONTROLE_RE = re.compile(r"^(\d{14})-\d+-(\d+)/(\d{4})$")


def parse_numero_controle(pncp_id: str) -> tuple[str, int, int]:
    match = _NUMERO_CONTROLE_RE.match(pncp_id)
    if not match:
        raise ValueError(f"numeroControlePNCP em formato inesperado: {pncp_id}")
    cnpj, sequencial, ano = match.groups()
    return cnpj, int(ano), int(sequencial)


def selecionar_documento_edital(arquivos: list[dict]) -> dict | None:
    candidatos = [a for a in arquivos if "edital" in a.get("titulo", "").lower()]
    return candidatos[0] if candidatos else None

MODALIDADES_LEI_14133 = {
    1: "Leilão - Eletrônico",
    2: "Diálogo Competitivo",
    3: "Concurso",
    4: "Concorrência - Eletrônica",
    5: "Concorrência - Presencial",
    6: "Pregão - Eletrônico",
    7: "Pregão - Presencial",
    8: "Dispensa",
    9: "Inexigibilidade",
    10: "Manifestação de Interesse",
    11: "Pré-qualificação",
    12: "Credenciamento",
    13: "Leilão - Presencial",
}

_ESFERA_POR_ID = {
    "F": Esfera.federal,
    "E": Esfera.estadual,
    "M": Esfera.municipal,
}


class PNCPRateLimitError(Exception):
    pass


def _link_pncp(cnpj: str, ano_compra: int, sequencial_compra: int) -> str:
    return f"https://pncp.gov.br/app/editais/{cnpj}/{ano_compra}/{sequencial_compra}"


def parse_contratacao(item: dict) -> dict:
    orgao = item["orgaoEntidade"]
    unidade = item["unidadeOrgao"]
    return {
        "pncp_id": item["numeroControlePNCP"],
        "orgao": orgao["razaoSocial"],
        "objeto": item["objetoCompra"],
        "esfera": _ESFERA_POR_ID.get(orgao.get("esferaId"), Esfera.municipal),
        "modalidade": item.get("modalidadeNome", ""),
        "uf": unidade["ufSigla"],
        "municipio": unidade.get("municipioNome"),
        "valor_estimado": item.get("valorTotalEstimado"),
        "data_publicacao": datetime.date.fromisoformat(item["dataPublicacaoPncp"][:10]),
        "link_pncp": _link_pncp(orgao["cnpj"], item["anoCompra"], item["sequencialCompra"]),
    }


# RF-01: cliente do PNCP usado pela Prospecção para buscar editais publicados
class PNCPClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        min_interval: float = 0.4,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url or settings.pncp_base_url, timeout=timeout, transport=transport
        )
        self._min_interval = min_interval
        self._last_request_at = 0.0

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PNCPClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

    def buscar_contratacoes_publicadas(
        self,
        data_inicial: datetime.date,
        data_final: datetime.date,
        codigo_modalidade: int,
        pagina: int = 1,
        tamanho_pagina: int = 50,
        max_tentativas: int = 5,
    ) -> dict:
        espera = 1.0
        for tentativa in range(max_tentativas + 1):
            self._throttle()
            try:
                response = self._client.get(
                    "/v1/contratacoes/publicacao",
                    params={
                        "dataInicial": data_inicial.strftime("%Y%m%d"),
                        "dataFinal": data_final.strftime("%Y%m%d"),
                        "codigoModalidadeContratacao": codigo_modalidade,
                        "pagina": pagina,
                        "tamanhoPagina": tamanho_pagina,
                    },
                )
            except httpx.TransportError:
                self._last_request_at = time.monotonic()
                if tentativa == max_tentativas:
                    raise
                time.sleep(espera)
                espera *= 2
                continue

            self._last_request_at = time.monotonic()
            if response.status_code == 429 or response.status_code >= 500:
                if tentativa == max_tentativas:
                    if response.status_code == 429:
                        raise PNCPRateLimitError("limite de requisições do PNCP excedido")
                    response.raise_for_status()
                time.sleep(espera)
                espera *= 2
                continue
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return {"data": [], "totalPaginas": 0}
            return response.json()
        raise PNCPRateLimitError("limite de requisições do PNCP excedido")

    def buscar_todas_paginas(
        self,
        data_inicial: datetime.date,
        data_final: datetime.date,
        codigo_modalidade: int,
        tamanho_pagina: int = 50,
        max_paginas: int | None = None,
    ) -> Iterator[dict]:
        pagina = 1
        while True:
            resultado = self.buscar_contratacoes_publicadas(
                data_inicial, data_final, codigo_modalidade, pagina, tamanho_pagina
            )
            yield from resultado["data"]
            if pagina >= resultado["totalPaginas"]:
                break
            if max_paginas is not None and pagina >= max_paginas:
                break
            pagina += 1

    # RF-ANL-01: lista os documentos (edital, ETP, anexos) de uma contratação.
    # Vive num host/path diferente da API de consulta (api/pncp, não api/consulta).
    def buscar_arquivos_compra(self, cnpj: str, ano: int, sequencial: int) -> list[dict]:
        response = self._client.get(
            f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/arquivos"
        )
        response.raise_for_status()
        return response.json()

    def baixar_arquivo(self, url: str) -> bytes:
        response = self._client.get(url)
        response.raise_for_status()
        return response.content
