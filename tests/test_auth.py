import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from data.auth import hash_senha, verificar_senha
from data.db import get_session
from webapp.main import app


def test_hash_senha_roundtrip():
    hash_ = hash_senha("segredo123")
    assert verificar_senha("segredo123", hash_)
    assert not verificar_senha("errada", hash_)


class _FakeQuery:
    def __init__(self, resultado):
        self._resultado = resultado

    def filter_by(self, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def one_or_none(self):
        return self._resultado

    def all(self):
        return self._resultado if isinstance(self._resultado, list) else [self._resultado]


class _FakeSession:
    def __init__(self, resultado=None):
        self._resultado = resultado

    def query(self, model):
        return _FakeQuery(self._resultado)


def _client_com_sessao(resultado=None):
    fake_session = _FakeSession(resultado)

    def _get_session_fake():
        yield fake_session

    app.dependency_overrides[get_session] = _get_session_fake
    return TestClient(app)


def test_login_submit_credenciais_erradas():
    client = _client_com_sessao(resultado=None)
    try:
        response = client.post(
            "/login", data={"email": "x@x.com", "senha": "errada"}, follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/login?erro=1"
    finally:
        app.dependency_overrides.clear()


def test_login_submit_credenciais_corretas():
    cliente_fake = SimpleNamespace(id=42, senha_hash=hash_senha("segredo123"))
    client = _client_com_sessao(resultado=cliente_fake)
    try:
        response = client.post(
            "/login", data={"email": "x@x.com", "senha": "segredo123"}, follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"
    finally:
        app.dependency_overrides.clear()


def test_dashboard_sem_sessao_redireciona_para_login():
    client = _client_com_sessao()
    try:
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"
    finally:
        app.dependency_overrides.clear()


def test_admin_sem_sessao_redireciona_para_login():
    client = _client_com_sessao()
    try:
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/login"
    finally:
        app.dependency_overrides.clear()


def test_raiz_redireciona_para_login():
    client = _client_com_sessao()
    try:
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/login"
    finally:
        app.dependency_overrides.clear()


def test_admin_login_submit_credenciais_corretas():
    operador_fake = SimpleNamespace(id=7, senha_hash=hash_senha("outrasenha123"))
    client = _client_com_sessao(resultado=operador_fake)
    try:
        response = client.post(
            "/admin/login",
            data={"email": "op@x.com", "senha": "outrasenha123"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/admin"
    finally:
        app.dependency_overrides.clear()


def test_admin_home_autenticado_lista_clientes():
    operador_fake = SimpleNamespace(id=7, senha_hash=hash_senha("outrasenha123"))
    client = _client_com_sessao(resultado=operador_fake)
    try:
        client.post(
            "/admin/login",
            data={"email": "op@x.com", "senha": "outrasenha123"},
            follow_redirects=False,
        )

        cliente_fake = SimpleNamespace(
            razao_social="Empresa X",
            email="e@x.com",
            cnpj="12345678000199",
            criado_em=datetime.datetime(2026, 1, 1),
        )
        fake_session_clientes = _FakeSession([cliente_fake])

        def _get_session_clientes():
            yield fake_session_clientes

        app.dependency_overrides[get_session] = _get_session_clientes

        response = client.get("/admin")
        assert response.status_code == 200
        assert "Empresa X" in response.text
    finally:
        app.dependency_overrides.clear()
