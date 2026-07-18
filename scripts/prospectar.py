#!/usr/bin/env python3
import fcntl
import logging
import sys
from pathlib import Path

from agents.prospeccao.agent import alertar_falha_operador, executar_varredura
from webapp.clients.pncp import PNCPClient
from webapp.clients.resend_client import ResendClient
from data.db import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("prospeccao")

JANELA_DIAS = 2
SCORE_MINIMO = 40.0
LOCKFILE = Path(__file__).resolve().parent.parent / "logs" / "prospectar.lock"


def main() -> None:
    session = SessionLocal()
    try:
        with PNCPClient() as pncp, ResendClient() as resend:
            resultado = executar_varredura(
                session, pncp, resend, janela_dias=JANELA_DIAS, score_minimo=SCORE_MINIMO
            )
        logger.info("varredura concluída: %d matches no total", resultado["matches"])
    finally:
        session.close()


if __name__ == "__main__":
    LOCKFILE.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(LOCKFILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        logger.warning("outra execução já em andamento, encerrando")
        sys.exit(0)

    try:
        main()
    except Exception:
        logger.exception("varredura falhou com erro não tratado")
        alertar_falha_operador()
        raise
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
