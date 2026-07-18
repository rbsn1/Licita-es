#!/usr/bin/env python3
import re
import sys

from sqlalchemy.exc import IntegrityError

from data.db import SessionLocal
from data.models import Cliente, PerfilCliente
from data.settings import settings

UFS_VALIDAS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


def perguntar(rotulo: str, obrigatorio: bool = True) -> str:
    while True:
        valor = input(f"{rotulo}: ").strip()
        if valor or not obrigatorio:
            return valor
        print("  esse campo é obrigatório.")


def perguntar_lista(rotulo: str) -> list[str]:
    valor = input(f"{rotulo} (separadas por vírgula): ").strip()
    if not valor:
        return []
    return [item.strip() for item in valor.split(",") if item.strip()]


def perguntar_ufs() -> list[str]:
    while True:
        brutas = perguntar_lista("UFs atendidas")
        ufs = [uf.upper() for uf in brutas]
        invalidas = [uf for uf in ufs if uf not in UFS_VALIDAS]
        if invalidas:
            print(f"  UF inválida: {', '.join(invalidas)}. Use siglas de 2 letras (ex: SP, RS).")
            continue
        return ufs


def perguntar_valor(rotulo: str) -> float | None:
    while True:
        valor = input(f"{rotulo} (deixe em branco se não houver): ").strip()
        if not valor:
            return None
        try:
            return float(valor.replace(".", "").replace(",", "."))
        except ValueError:
            print("  valor inválido, use só números (ex: 50000 ou 50.000,00).")


def normalizar_cnpj(bruto: str) -> str:
    return re.sub(r"\D", "", bruto)


def main() -> None:
    print("=== Cadastro de cliente — agente de prospecção ===\n")

    razao_social = perguntar("Razão social")

    while True:
        cnpj = normalizar_cnpj(perguntar("CNPJ"))
        if len(cnpj) == 14:
            break
        print("  CNPJ inválido, deve ter 14 dígitos.")

    while True:
        email = perguntar("E-mail para receber os alertas")
        if "@" in email and "." in email.split("@")[-1]:
            break
        print("  e-mail parece inválido, tente novamente.")

    ufs = perguntar_ufs()
    palavras_chave = perguntar_lista("Palavras-chave do ramo de atuação")
    valor_minimo = perguntar_valor("Valor mínimo de interesse")
    valor_maximo = perguntar_valor("Valor máximo de interesse")

    session = SessionLocal()
    cliente = Cliente(razao_social=razao_social, cnpj=cnpj, email=email)
    session.add(cliente)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        print(f"\nJá existe um cliente cadastrado com o CNPJ {cnpj}.")
        session.close()
        sys.exit(1)

    perfil = PerfilCliente(
        cliente_id=cliente.id,
        cnaes=[],
        ufs=ufs,
        palavras_chave=palavras_chave,
        valor_minimo=valor_minimo,
        valor_maximo=valor_maximo,
    )
    session.add(perfil)
    session.commit()

    dashboard_url = f"{settings.dashboard_base_url}/dashboard/{cliente.access_token}"
    print(f"\nCliente cadastrado com sucesso (id={cliente.id}).")
    print(f"Painel do cliente: {dashboard_url}")
    print("A próxima varredura do cron já vai considerar esse perfil.")
    session.close()


if __name__ == "__main__":
    main()
