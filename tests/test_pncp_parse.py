import datetime

from webapp.clients.pncp import parse_contratacao
from data.models import Esfera

ITEM_EXEMPLO = {
    "orgaoEntidade": {
        "cnpj": "83021808000182",
        "razaoSocial": "MUNICIPIO DE CHAPECO",
        "esferaId": "M",
    },
    "unidadeOrgao": {
        "ufSigla": "SC",
        "municipioNome": "Chapecó",
    },
    "anoCompra": 2026,
    "sequencialCompra": 378,
    "numeroControlePNCP": "83021808000182-1-000378/2026",
    "objetoCompra": "AQUISIÇÃO DE SPRAYS DE DEFESA PESSOAL",
    "valorTotalEstimado": 94077.8,
    "modalidadeNome": "Pregão - Eletrônico",
    "dataPublicacaoPncp": "2026-07-15T00:00:19",
}


def test_parse_contratacao_mapeia_campos_corretamente():
    resultado = parse_contratacao(ITEM_EXEMPLO)
    assert resultado["pncp_id"] == "83021808000182-1-000378/2026"
    assert resultado["orgao"] == "MUNICIPIO DE CHAPECO"
    assert resultado["esfera"] == Esfera.municipal
    assert resultado["modalidade"] == "Pregão - Eletrônico"
    assert resultado["uf"] == "SC"
    assert resultado["municipio"] == "Chapecó"
    assert resultado["valor_estimado"] == 94077.8
    assert resultado["data_publicacao"] == datetime.date(2026, 7, 15)
    assert resultado["link_pncp"] == "https://pncp.gov.br/app/editais/83021808000182/2026/378"


def test_parse_contratacao_mapeia_esfera_federal_e_estadual():
    item_federal = {**ITEM_EXEMPLO, "orgaoEntidade": {**ITEM_EXEMPLO["orgaoEntidade"], "esferaId": "F"}}
    item_estadual = {**ITEM_EXEMPLO, "orgaoEntidade": {**ITEM_EXEMPLO["orgaoEntidade"], "esferaId": "E"}}
    assert parse_contratacao(item_federal)["esfera"] == Esfera.federal
    assert parse_contratacao(item_estadual)["esfera"] == Esfera.estadual


def test_parse_contratacao_esfera_desconhecida_cai_para_municipal():
    item = {**ITEM_EXEMPLO, "orgaoEntidade": {**ITEM_EXEMPLO["orgaoEntidade"], "esferaId": "X"}}
    assert parse_contratacao(item)["esfera"] == Esfera.municipal


def test_parse_contratacao_sem_valor_estimado():
    item = {k: v for k, v in ITEM_EXEMPLO.items() if k != "valorTotalEstimado"}
    assert parse_contratacao(item)["valor_estimado"] is None
