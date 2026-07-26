import datetime

import httpx

_BASE_URL = "https://dadosabertos.compras.gov.br"


# RF-PRE-01: cliente do Painel de Preços (Compras.gov.br/SIASG) — API pública de
# dados abertos, usada como fonte complementar de preços de referência. Consulta
# por codigoItemCatalogo (CATMAT/CATSER), único filtro por item que a API aceita
# — não há busca por texto livre do objeto.
class PainelPrecosClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url or _BASE_URL, timeout=timeout, transport=transport
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PainelPrecosClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _consultar(
        self,
        caminho: str,
        codigo_item_catalogo: int,
        data_compra_inicio: datetime.date | None,
        data_compra_fim: datetime.date | None,
        pagina: int,
        tamanho_pagina: int,
    ) -> dict:
        params: dict[str, str | int] = {
            "codigoItemCatalogo": codigo_item_catalogo,
            "pagina": pagina,
            "tamanhoPagina": tamanho_pagina,
        }
        if data_compra_inicio:
            params["dataCompraInicio"] = data_compra_inicio.isoformat()
        if data_compra_fim:
            params["dataCompraFim"] = data_compra_fim.isoformat()

        response = self._client.get(caminho, params=params)
        response.raise_for_status()
        return response.json()

    def consultar_material(
        self,
        codigo_item_catalogo: int,
        data_compra_inicio: datetime.date | None = None,
        data_compra_fim: datetime.date | None = None,
        pagina: int = 1,
        tamanho_pagina: int = 50,
    ) -> dict:
        return self._consultar(
            "/modulo-pesquisa-preco/1_consultarMaterial",
            codigo_item_catalogo,
            data_compra_inicio,
            data_compra_fim,
            pagina,
            tamanho_pagina,
        )

    def consultar_servico(
        self,
        codigo_item_catalogo: int,
        data_compra_inicio: datetime.date | None = None,
        data_compra_fim: datetime.date | None = None,
        pagina: int = 1,
        tamanho_pagina: int = 50,
    ) -> dict:
        return self._consultar(
            "/modulo-pesquisa-preco/3_consultarServico",
            codigo_item_catalogo,
            data_compra_inicio,
            data_compra_fim,
            pagina,
            tamanho_pagina,
        )

    # RF-PRE-01: preços unitários praticados para o item de catálogo, usados como
    # sinal complementar (não somado diretamente à faixa de valor total, que vem
    # do histórico de contratos do PNCP — unidades diferentes: preço unitário vs.
    # valor total do contrato)
    def buscar_precos_unitarios(
        self,
        codigo_item_catalogo: int,
        tipo: str = "material",
        data_compra_inicio: datetime.date | None = None,
        data_compra_fim: datetime.date | None = None,
        max_paginas: int = 5,
    ) -> list[float]:
        consultar = self.consultar_material if tipo == "material" else self.consultar_servico
        precos: list[float] = []
        pagina = 1
        while pagina <= max_paginas:
            resultado = consultar(
                codigo_item_catalogo, data_compra_inicio, data_compra_fim, pagina
            )
            itens = resultado.get("resultado", [])
            precos.extend(
                item["precoUnitario"] for item in itens if item.get("precoUnitario") is not None
            )
            if pagina >= resultado.get("totalPaginas", 0):
                break
            pagina += 1
        return precos
