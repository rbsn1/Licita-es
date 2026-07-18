import io
import json

import anthropic
from pypdf import PdfReader

from webapp.clients.pncp import (
    PNCPClient,
    parse_numero_controle,
    selecionar_documento_edital,
)
from data.settings import settings

ESQUEMA_RESUMO_EDITAL = {
    "type": "object",
    "properties": {
        "prazo_limite_proposta": {
            "type": ["string", "null"],
            "description": "Data e hora limite para envio de propostas, se identificável no texto do edital",
        },
        "valor_estimado": {
            "type": ["number", "null"],
            "description": "Valor total estimado do objeto da licitação, em reais, se informado no edital",
        },
        "requisitos_habilitacao": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Documentos/requisitos exigidos para habilitação (jurídica, fiscal, técnica, econômico-financeira)",
        },
        "clausulas_risco": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Cláusulas potencialmente restritivas ou de risco para o licitante (prazos exíguos, exigências desproporcionais, penalidades severas etc.)",
        },
    },
    "required": [
        "prazo_limite_proposta",
        "valor_estimado",
        "requisitos_habilitacao",
        "clausulas_risco",
    ],
    "additionalProperties": False,
}


def extrair_texto_pdf(conteudo: bytes) -> str:
    leitor = PdfReader(io.BytesIO(conteudo))
    return "\n".join(pagina.extract_text() or "" for pagina in leitor.pages)


# RF-ANL-01: extrai prazo, valor estimado, requisitos de habilitação e cláusulas
# de risco do texto do edital, produzindo um resumo estruturado
def analisar_texto_edital(client: anthropic.Anthropic, texto_edital: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        output_config={"format": {"type": "json_schema", "schema": ESQUEMA_RESUMO_EDITAL}},
        messages=[
            {
                "role": "user",
                "content": (
                    "Extraia do texto de edital de licitação pública abaixo: prazo limite "
                    "para envio de propostas, valor estimado, requisitos de habilitação "
                    "e cláusulas potencialmente restritivas ou de risco para o licitante.\n\n"
                    f"{texto_edital}"
                ),
            }
        ],
    )
    texto_json = next(bloco.text for bloco in response.content if bloco.type == "text")
    return json.loads(texto_json)


# RF-ANL-01: pipeline completo — obtém o PDF do edital automaticamente via PNCP
# a partir do link produzido pela Prospecção e produz o resumo estruturado
def analisar_edital_por_numero_controle(
    pncp: PNCPClient, client: anthropic.Anthropic, numero_controle_pncp: str
) -> dict:
    cnpj, ano, sequencial = parse_numero_controle(numero_controle_pncp)
    arquivos = pncp.buscar_arquivos_compra(cnpj, ano, sequencial)
    documento_edital = selecionar_documento_edital(arquivos)
    if documento_edital is None:
        raise ValueError(f"nenhum documento de edital encontrado para {numero_controle_pncp}")

    conteudo = pncp.baixar_arquivo(documento_edital["url"])
    texto = extrair_texto_pdf(conteudo)
    return analisar_texto_edital(client, texto)


def criar_cliente_anthropic() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)
