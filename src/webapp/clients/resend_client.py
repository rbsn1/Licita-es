import httpx

from data.settings import settings


# RF-03: canal de e-mail usado para os alertas de edital compatível
class ResendClient:
    def __init__(
        self,
        api_key: str | None = None,
        from_email: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._from_email = from_email or settings.resend_from_email
        self._client = httpx.Client(
            base_url="https://api.resend.com",
            headers={"Authorization": f"Bearer {api_key or settings.resend_api_key}"},
            timeout=15.0,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ResendClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def enviar_email(self, destinatario: str, assunto: str, corpo_html: str) -> dict:
        response = self._client.post(
            "/emails",
            json={
                "from": self._from_email,
                "to": [destinatario],
                "subject": assunto,
                "html": corpo_html,
            },
        )
        response.raise_for_status()
        return response.json()
