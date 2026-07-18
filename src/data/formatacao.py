def formatar_valor_brl(valor: float | None) -> str:
    if not valor:
        return "não informado"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
