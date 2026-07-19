from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from data.db import get_session
from data.models import Cliente

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


# RF-AUTH-03: painel administrativo lista os clientes cadastrados a partir da
# sessão autenticada do operador. Só leitura por ora — cadastro de cliente
# continua via scripts/cadastrar_cliente.py (ver itens em aberto do spec)
@router.get("/admin")
def admin_home(request: Request, session: Session = Depends(get_session)):
    if not request.session.get("operador_id"):
        return RedirectResponse(url="/admin/login", status_code=303)

    clientes = session.query(Cliente).order_by(Cliente.criado_em.desc()).all()
    return templates.TemplateResponse(request, "admin.html", {"clientes": clientes})
