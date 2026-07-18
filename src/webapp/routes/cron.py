import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from agents.prospeccao.agent import alertar_falha_operador, executar_varredura
from data.db import get_session
from data.settings import settings
from webapp.clients.pncp import PNCPClient
from webapp.clients.resend_client import ResendClient

router = APIRouter()
logger = logging.getLogger(__name__)


# RNF-01: dispara a varredura intradiária via Vercel Cron. O header Authorization
# é injetado automaticamente pelo Vercel a partir da env var CRON_SECRET.
@router.get("/cron/prospectar")
def cron_prospectar(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> dict:
    if not settings.cron_secret or authorization != f"Bearer {settings.cron_secret}":
        raise HTTPException(status_code=401, detail="não autorizado")

    try:
        with PNCPClient() as pncp, ResendClient() as resend:
            return executar_varredura(session, pncp, resend)
    except Exception:
        logger.exception("varredura via cron falhou")
        alertar_falha_operador()
        raise HTTPException(status_code=500, detail="varredura falhou, operador notificado")
