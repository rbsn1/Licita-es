from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from data.settings import settings
from webapp.routes.admin import router as admin_router
from webapp.routes.auth import router as auth_router
from webapp.routes.cron import router as cron_router
from webapp.routes.dashboard import router as dashboard_router

app = FastAPI(title="Agente de Prospecção de Editais")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
app.include_router(dashboard_router)
app.include_router(cron_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
