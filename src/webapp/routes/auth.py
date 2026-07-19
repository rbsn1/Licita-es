from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from data.auth import verificar_senha
from data.db import get_session
from data.models import Cliente, Operador

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


# RF-AUTH-01: login do cliente final por e-mail e senha
@router.get("/login")
def login_form(request: Request, erro: bool = False):
    return templates.TemplateResponse(request, "login.html", {"erro": erro})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    cliente = session.query(Cliente).filter_by(email=email).one_or_none()
    if cliente is None or not cliente.senha_hash or not verificar_senha(senha, cliente.senha_hash):
        return RedirectResponse(url="/login?erro=1", status_code=303)
    request.session["cliente_id"] = cliente.id
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.pop("cliente_id", None)
    return RedirectResponse(url="/login", status_code=303)


# RF-AUTH-02: login do operador da consultoria por e-mail e senha
@router.get("/admin/login")
def admin_login_form(request: Request, erro: bool = False):
    return templates.TemplateResponse(request, "admin_login.html", {"erro": erro})


@router.post("/admin/login")
def admin_login_submit(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    operador = session.query(Operador).filter_by(email=email).one_or_none()
    if operador is None or not verificar_senha(senha, operador.senha_hash):
        return RedirectResponse(url="/admin/login?erro=1", status_code=303)
    request.session["operador_id"] = operador.id
    return RedirectResponse(url="/admin", status_code=303)


@router.get("/admin/logout")
def admin_logout(request: Request):
    request.session.pop("operador_id", None)
    return RedirectResponse(url="/admin/login", status_code=303)
