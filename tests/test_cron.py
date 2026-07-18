from fastapi.testclient import TestClient

from data.db import get_session
from data.settings import settings
from webapp.main import app


def _client_com_sessao_fake() -> TestClient:
    app.dependency_overrides[get_session] = lambda: iter([object()])
    return TestClient(app)


def test_cron_prospectar_sem_cron_secret_configurado_retorna_401(monkeypatch):
    monkeypatch.setattr(settings, "cron_secret", "")
    client = _client_com_sessao_fake()
    try:
        response = client.get("/cron/prospectar", headers={"Authorization": "Bearer qualquer-coisa"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_cron_prospectar_com_secret_errado_retorna_401(monkeypatch):
    monkeypatch.setattr(settings, "cron_secret", "segredo-correto")
    client = _client_com_sessao_fake()
    try:
        response = client.get("/cron/prospectar", headers={"Authorization": "Bearer segredo-errado"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_cron_prospectar_sem_header_retorna_401(monkeypatch):
    monkeypatch.setattr(settings, "cron_secret", "segredo-correto")
    client = _client_com_sessao_fake()
    try:
        response = client.get("/cron/prospectar")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
