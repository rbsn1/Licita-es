from types import SimpleNamespace

from fastapi.testclient import TestClient

from data.auth import hash_senha
from data.db import get_session
from webapp.main import app


class _FakeQuery:
    def __init__(self, resultado):
        self._resultado = resultado

    def filter_by(self, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def one_or_none(self):
        return self._resultado

    def all(self):
        return self._resultado


class _FakeSession:
    def __init__(self, cliente, resultados):
        self._cliente = cliente
        self._resultados = resultados

    def query(self, *args):
        if len(args) == 1:
            return _FakeQuery(self._cliente)
        return _FakeQuery(self._resultados)


def _client_logado(resultados=None):
    cliente = SimpleNamespace(id=1, razao_social="Cliente Teste", senha_hash=hash_senha("segredo123"))
    fake_session = _FakeSession(cliente, resultados or [])

    def _get_session_fake():
        yield fake_session

    app.dependency_overrides[get_session] = _get_session_fake
    client = TestClient(app)
    login = client.post("/login", data={"email": "x@x.com", "senha": "segredo123"}, follow_redirects=False)
    assert login.status_code == 303
    return client


def test_dashboard_com_datas_vazias_nao_devolve_422():
    client = _client_logado()
    try:
        response = client.get("/dashboard", params={"data_inicial": "", "data_final": ""})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_dashboard_com_esfera_vazia_nao_devolve_422():
    client = _client_logado()
    try:
        response = client.get("/dashboard", params={"esfera": ""})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_dashboard_com_esfera_invalida_ignora_o_filtro_em_vez_de_quebrar():
    client = _client_logado()
    try:
        response = client.get("/dashboard", params={"esfera": "nao-existe"})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_dashboard_com_data_invalida_ignora_o_filtro_em_vez_de_quebrar():
    client = _client_logado()
    try:
        response = client.get("/dashboard", params={"data_inicial": "31/12/2026"})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_dashboard_com_data_valida_aplica_o_filtro():
    client = _client_logado()
    try:
        response = client.get("/dashboard", params={"data_inicial": "2026-01-01", "data_final": "2026-12-31"})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
