from agents.prospeccao.agent import ProspeccaoAgent
from data.models import PerfilCliente

agent = ProspeccaoAgent(pncp_client=None)


def _perfil(**kwargs):
    base = dict(
        cliente_id=1, cnaes=[], ufs=[], palavras_chave=[], valor_minimo=None, valor_maximo=None
    )
    base.update(kwargs)
    return PerfilCliente(**base)


def _edital(**kwargs):
    base = dict(
        pncp_id="1",
        orgao="Órgão Teste",
        objeto="Aquisição de material de informática",
        uf="SP",
        valor_estimado=50000.0,
    )
    base.update(kwargs)
    return base


def test_score_zero_sem_criterios_configurados():
    assert agent.calcular_score(_edital(), _perfil()) == 0.0


def test_score_palavra_chave_bate_totalmente():
    perfil = _perfil(palavras_chave=["informática"])
    assert agent.calcular_score(_edital(), perfil) == 100.0


def test_score_palavra_chave_bate_parcialmente():
    perfil = _perfil(palavras_chave=["informática", "impressora"])
    assert agent.calcular_score(_edital(), perfil) == 50.0


def test_score_uf_com_match():
    perfil = _perfil(ufs=["SP"])
    assert agent.calcular_score(_edital(uf="SP"), perfil) == 100.0


def test_score_uf_sem_match():
    perfil = _perfil(ufs=["RJ"])
    assert agent.calcular_score(_edital(uf="SP"), perfil) == 0.0


def test_score_valor_dentro_da_faixa():
    perfil = _perfil(valor_minimo=1000, valor_maximo=100000)
    assert agent.calcular_score(_edital(valor_estimado=50000), perfil) == 100.0


def test_score_valor_fora_da_faixa():
    perfil = _perfil(valor_minimo=1000, valor_maximo=10000)
    assert agent.calcular_score(_edital(valor_estimado=50000), perfil) == 0.0


def test_score_valor_ausente_conta_como_fora_da_faixa():
    perfil = _perfil(valor_maximo=100000)
    assert agent.calcular_score(_edital(valor_estimado=None), perfil) == 0.0


def test_score_combina_pesos_dos_criterios_ativos():
    perfil = _perfil(palavras_chave=["informática"], ufs=["RJ"], valor_minimo=1000, valor_maximo=100000)
    # palavra-chave bate (peso 0.5), UF não bate (peso 0.3), valor bate (peso 0.2)
    esperado = round((1 * 0.5 + 0 * 0.3 + 1 * 0.2) / 1.0 * 100, 2)
    assert agent.calcular_score(_edital(uf="SP", valor_estimado=50000), perfil) == esperado


def test_filtrar_compativeis_aplica_threshold_e_ordena_por_score():
    perfil = _perfil(palavras_chave=["informática"])
    editais = [
        _edital(pncp_id="1", objeto="nada a ver aqui"),
        _edital(pncp_id="2", objeto="material de informática"),
    ]
    resultado = agent.filtrar_compativeis(editais, perfil, score_minimo=50)
    assert len(resultado) == 1
    assert resultado[0][0]["pncp_id"] == "2"


def test_filtrar_compativeis_ordena_do_maior_pro_menor_score():
    perfil = _perfil(palavras_chave=["informática"], ufs=["SP"])
    editais = [
        _edital(pncp_id="so-palavra", objeto="material de informática", uf="RJ"),
        _edital(pncp_id="palavra-e-uf", objeto="material de informática", uf="SP"),
    ]
    resultado = agent.filtrar_compativeis(editais, perfil, score_minimo=0)
    assert [edital["pncp_id"] for edital, _ in resultado] == ["palavra-e-uf", "so-palavra"]
