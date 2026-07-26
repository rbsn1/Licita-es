import datetime
from types import SimpleNamespace

import anthropic
import httpx

import agents.pipeline as pipeline_module
from agents.pipeline import (
    _parse_prazo,
    analisar_editais_pendentes,
    precificar_editais_pendentes,
    processar_editais_pendentes,
)


def _erro_credito_insuficiente() -> anthropic.APIStatusError:
    response = httpx.Response(
        400,
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
        json={"error": {"message": "Your credit balance is too low to access the Anthropic API."}},
    )
    return anthropic.BadRequestError(
        "Your credit balance is too low to access the Anthropic API.", response=response, body=None
    )


class _FakeQuery:
    def __init__(self, resultado):
        self._resultado = resultado

    def join(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def limit(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self._resultado


class _FakeSession:
    def __init__(self, resultados):
        self._resultados = list(resultados)
        self.adicionados = []
        self.commits = 0
        self.rollbacks = 0

    def query(self, *args):
        return _FakeQuery(self._resultados.pop(0))

    def add(self, obj):
        self.adicionados.append(obj)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _edital(id=1, pncp_id="83102277000152-1-000424/2026", objeto="Aquisição de material", valor_estimado=100000.0):
    return SimpleNamespace(id=id, pncp_id=pncp_id, objeto=objeto, valor_estimado=valor_estimado)


def test_parse_prazo_iso_valido():
    assert _parse_prazo("2026-08-01T09:00:00") == datetime.datetime(2026, 8, 1, 9, 0, 0)


def test_parse_prazo_none():
    assert _parse_prazo(None) is None


def test_parse_prazo_formato_inesperado_retorna_none():
    assert _parse_prazo("data inválida") is None


def test_analisar_editais_pendentes_persiste_resumo_por_edital(monkeypatch):
    editais = [_edital(id=1), _edital(id=2, pncp_id="83102277000152-1-000425/2026")]
    session = _FakeSession(resultados=[editais])

    respostas = {
        "83102277000152-1-000424/2026": {
            "prazo_limite_proposta": "2026-08-01T09:00:00",
            "valor_estimado": 90000.0,
            "requisitos_habilitacao": ["CND federal"],
            "clausulas_risco": ["Prazo exíguo"],
        },
        "83102277000152-1-000425/2026": {
            "prazo_limite_proposta": None,
            "valor_estimado": None,
            "requisitos_habilitacao": [],
            "clausulas_risco": [],
        },
    }

    def fake_analisar(pncp, anthropic_client, numero_controle):
        return respostas[numero_controle]

    monkeypatch.setattr(pipeline_module, "analisar_edital_por_numero_controle", fake_analisar)

    total = analisar_editais_pendentes(session, pncp=object(), anthropic_client=object())

    assert total == 2
    assert session.commits == 2
    assert len(session.adicionados) == 2
    assert session.adicionados[0].edital_id == 1
    assert session.adicionados[0].valor_estimado == 90000.0
    assert session.adicionados[1].requisitos_habilitacao == []


def test_analisar_editais_pendentes_falha_num_edital_nao_interrompe_os_demais(monkeypatch):
    editais = [_edital(id=1), _edital(id=2, pncp_id="83102277000152-1-000425/2026")]
    session = _FakeSession(resultados=[editais])

    def fake_analisar(pncp, anthropic_client, numero_controle):
        if numero_controle.endswith("424/2026"):
            raise ValueError("PDF ilegível")
        return {
            "prazo_limite_proposta": None,
            "valor_estimado": None,
            "requisitos_habilitacao": [],
            "clausulas_risco": [],
        }

    monkeypatch.setattr(pipeline_module, "analisar_edital_por_numero_controle", fake_analisar)

    total = analisar_editais_pendentes(session, pncp=object(), anthropic_client=object())

    assert total == 1
    assert len(session.adicionados) == 1
    assert session.adicionados[0].edital_id == 2


def test_analisar_editais_pendentes_para_no_primeiro_erro_de_credito_e_alerta_operador(monkeypatch):
    editais = [_edital(id=1), _edital(id=2, pncp_id="83102277000152-1-000425/2026")]
    session = _FakeSession(resultados=[editais])

    def fake_analisar(pncp, anthropic_client, numero_controle):
        raise _erro_credito_insuficiente()

    alertas = []
    monkeypatch.setattr(pipeline_module, "analisar_edital_por_numero_controle", fake_analisar)
    monkeypatch.setattr(
        pipeline_module,
        "_alertar_credito_insuficiente",
        lambda pendentes, processados: alertas.append((pendentes, processados)),
    )

    total = analisar_editais_pendentes(session, pncp=object(), anthropic_client=object())

    assert total == 0
    assert session.adicionados == []
    assert alertas == [(2, 0)]


def test_analisar_editais_pendentes_erro_generico_nao_dispara_alerta_de_credito(monkeypatch):
    editais = [_edital(id=1)]
    session = _FakeSession(resultados=[editais])

    def fake_analisar(pncp, anthropic_client, numero_controle):
        raise ValueError("PDF ilegível")

    alertas = []
    monkeypatch.setattr(pipeline_module, "analisar_edital_por_numero_controle", fake_analisar)
    monkeypatch.setattr(
        pipeline_module,
        "_alertar_credito_insuficiente",
        lambda pendentes, processados: alertas.append((pendentes, processados)),
    )

    total = analisar_editais_pendentes(session, pncp=object(), anthropic_client=object())

    assert total == 0
    assert alertas == []


def _resumo(valor_estimado=None):
    return SimpleNamespace(valor_estimado=valor_estimado)


class _FakePrecificacaoAgent:
    def __init__(self, resultado=None, excecao=None):
        self._resultado = resultado
        self._excecao = excecao
        self.chamadas = []

    def calcular_para_edital(self, edital, **kwargs):
        self.chamadas.append(edital)
        if self._excecao:
            raise self._excecao
        return self._resultado


def test_precificar_editais_pendentes_usa_valor_estimado_do_resumo_quando_presente():
    edital = _edital(id=1, valor_estimado=100000.0)
    resumo = _resumo(valor_estimado=90000.0)
    session = _FakeSession(resultados=[[(edital, resumo)]])
    agent = _FakePrecificacaoAgent(
        resultado={"minimo": 80000.0, "ideal": 88000.0, "maximo": 90000.0, "confiavel": True, "amostra": 3}
    )

    total = precificar_editais_pendentes(session, agent)

    assert total == 1
    assert agent.chamadas[0]["valor_estimado"] == 90000.0
    assert session.adicionados[0].edital_id == 1
    assert session.adicionados[0].ideal == 88000.0


def test_precificar_editais_pendentes_cai_para_valor_estimado_do_edital_sem_resumo():
    edital = _edital(id=1, valor_estimado=100000.0)
    resumo = _resumo(valor_estimado=None)
    session = _FakeSession(resultados=[[(edital, resumo)]])
    agent = _FakePrecificacaoAgent(
        resultado={"minimo": None, "ideal": None, "maximo": None, "confiavel": False, "amostra": 0}
    )

    precificar_editais_pendentes(session, agent)

    assert agent.chamadas[0]["valor_estimado"] == 100000.0


def test_precificar_editais_pendentes_falha_faz_rollback_e_continua():
    edital = _edital(id=1)
    resumo = _resumo()
    session = _FakeSession(resultados=[[(edital, resumo)]])
    agent = _FakePrecificacaoAgent(excecao=RuntimeError("PNCP fora do ar"))

    total = precificar_editais_pendentes(session, agent)

    assert total == 0
    assert session.rollbacks == 1
    assert session.adicionados == []


def test_processar_editais_pendentes_encadeia_analise_e_precificacao(monkeypatch):
    session = _FakeSession(resultados=[[], []])

    total = processar_editais_pendentes(session, pncp=object(), anthropic_client=object(), precificacao=_FakePrecificacaoAgent())

    assert total == {"analisados": 0, "precificados": 0}
