#!/usr/bin/env python3
import datetime
import fcntl
import logging
import sys
import traceback
from pathlib import Path

from agents.prospeccao.agent import ProspeccaoAgent, enviar_alertas_pendentes
from api.clients.pncp import PNCPClient
from api.clients.resend_client import ResendClient
from data.db import SessionLocal
from data.models import Cliente
from data.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("prospeccao")

JANELA_DIAS = 2
SCORE_MINIMO = 40.0
LOCKFILE = Path(__file__).resolve().parent.parent / "logs" / "prospectar.lock"


def main() -> None:
    session = SessionLocal()
    hoje = datetime.date.today()
    data_inicial = hoje - datetime.timedelta(days=JANELA_DIAS - 1)

    clientes = session.query(Cliente).join(Cliente.perfil).all()
    if not clientes:
        logger.info("nenhum cliente com perfil cadastrado, encerrando")
        session.close()
        return

    with PNCPClient() as pncp:
        agent = ProspeccaoAgent(pncp)
        logger.info("buscando editais publicados de %s a %s", data_inicial, hoje)
        editais = agent.buscar_editais_publicados(data_inicial, hoje)
        logger.info("editais encontrados: %d", len(editais))

        total_matches = 0
        for cliente in clientes:
            compativeis = agent.filtrar_compativeis(
                editais, cliente.perfil, score_minimo=SCORE_MINIMO
            )
            matches = agent.persistir_resultados(session, cliente.id, compativeis)
            total_matches += len(matches)
            logger.info("cliente %s: %d editais compatíveis", cliente.razao_social, len(matches))

    with ResendClient() as resend:
        enviados = enviar_alertas_pendentes(session, resend, limite=200)
        logger.info("alertas enviados: %d", enviados)

    session.close()
    logger.info("varredura concluída: %d matches no total", total_matches)


def alertar_falha_operador() -> None:
    if not settings.operador_email:
        logger.warning("OPERADOR_EMAIL não configurado, alerta de falha não enviado")
        return
    try:
        with ResendClient() as resend:
            resend.enviar_email(
                destinatario=settings.operador_email,
                assunto="[prospecção] falha na varredura do cron",
                corpo_html=f"<pre>{traceback.format_exc()}</pre>",
            )
    except Exception:
        logger.exception("falha ao enviar o alerta de falha para o operador")


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
