from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    pncp_base_url: str = "https://pncp.gov.br/api/consulta"
    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"
    dashboard_base_url: str = "http://localhost:8000"
    operador_email: str = ""


settings = Settings()
