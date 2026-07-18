from fastapi import FastAPI

from webapp.routes.cron import router as cron_router
from webapp.routes.dashboard import router as dashboard_router

app = FastAPI(title="Agente de Prospecção de Editais")
app.include_router(dashboard_router)
app.include_router(cron_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
