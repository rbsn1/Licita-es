from fastapi import FastAPI

from webapp.routes.dashboard import router as dashboard_router

app = FastAPI(title="Agente de Prospecção de Editais")
app.include_router(dashboard_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
