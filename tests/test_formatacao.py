from data.formatacao import formatar_valor_brl


def test_formatar_valor_brl_com_milhar():
    assert formatar_valor_brl(450000.0) == "R$ 450.000,00"


def test_formatar_valor_brl_sem_milhar():
    assert formatar_valor_brl(89.5) == "R$ 89,50"


def test_formatar_valor_brl_none():
    assert formatar_valor_brl(None) == "não informado"
