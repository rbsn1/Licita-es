#!/usr/bin/env python3
import getpass
import sys

from sqlalchemy.exc import IntegrityError

from data.auth import hash_senha
from data.db import SessionLocal
from data.models import Operador
from data.settings import settings


def main() -> None:
    print("=== Cadastro de operador — painel administrativo ===\n")

    while True:
        email = input("E-mail: ").strip()
        if "@" in email and "." in email.split("@")[-1]:
            break
        print("  e-mail parece inválido, tente novamente.")

    while True:
        senha = getpass.getpass("Senha (mín. 8 caracteres): ")
        if len(senha) >= 8:
            break
        print("  senha muito curta, use pelo menos 8 caracteres.")

    session = SessionLocal()
    operador = Operador(email=email, senha_hash=hash_senha(senha))
    session.add(operador)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        print(f"\nJá existe um operador cadastrado com o e-mail {email}.")
        session.close()
        sys.exit(1)

    print(f"\nOperador cadastrado com sucesso (id={operador.id}).")
    print(f"Login do painel administrativo: {settings.dashboard_base_url}/admin/login")
    session.close()


if __name__ == "__main__":
    main()
