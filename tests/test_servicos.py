"""Testes dos serviços (casos de uso) com repositórios em memória.

Inclui o cenário pedido no enunciado (exceto o reinício da aplicação, que
exige o banco real e está em ``test_integracao_postgres.py``).
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from happy_green.dominio import Competencia, Despesa, Receita, TipoLancamento, hoje
from happy_green.excecoes import (
    CategoriaIncompativelError,
    ExclusaoNaoPermitidaError,
    RegistroDuplicadoError,
    RegistroNaoEncontradoError,
)
from happy_green.repositorios import FiltroLancamentos
from happy_green.servicos import montar_servicos
from tests.fakes import criar_repositorios_em_memoria


@pytest.fixture
def servicos():
    return montar_servicos(*criar_repositorios_em_memoria())


@pytest.fixture
def base(servicos):
    conta = servicos.contas.criar("Conta Corrente", "0")
    salario = servicos.categorias.criar("Salário", "receita")
    alimentacao = servicos.categorias.criar("Alimentação", "despesa")
    transporte = servicos.categorias.criar("Transporte", "despesa")
    return conta, salario, alimentacao, transporte


def saldo(servicos, conta_id):
    return dict((c.id, s) for c, s in servicos.contas.listar_com_saldo())[conta_id]


# ===================================================== cenário do enunciado
def test_cenario_do_enunciado(servicos, base):
    conta, salario, alimentacao, transporte = base
    dia, mes = hoje(), Competencia.atual()

    # 1) conta com saldo inicial zero
    assert saldo(servicos, conta.id) == Decimal("0.00")

    # 2-4) receita 1.500,00; alimentação 300,00; transporte 120,00
    servicos.lancamentos.registrar("receita", "Salário", "1.500,00", dia, conta.id, salario.id)
    mercado = servicos.lancamentos.registrar("despesa", "Mercado", "300,00", dia, conta.id, alimentacao.id)
    onibus = servicos.lancamentos.registrar("despesa", "Ônibus", "120,00", dia, conta.id, transporte.id)
    assert isinstance(mercado, Despesa)

    # 5) saldo de 1.080,00
    assert saldo(servicos, conta.id) == Decimal("1080.00")

    # 6) orçamento de alimentação de 250,00 -> aviso de limite ultrapassado
    servicos.orcamentos.definir(alimentacao.id, mes, "250,00")
    (_, situacao), = servicos.orcamentos.acompanhar(mes)
    assert situacao.ultrapassado and situacao.excedente == Decimal("50.00")
    assert len(servicos.relatorios.painel(mes).orcamentos_ultrapassados) == 1

    # 7) transporte alterado para 150,00 -> saldo 1.050,00
    servicos.lancamentos.editar(onibus.id, "Ônibus", "150,00", dia, conta.id, transporte.id)
    assert saldo(servicos, conta.id) == Decimal("1050.00")

    # 8) exclui alimentação -> saldo 1.350,00 e orçamento atualizado
    servicos.lancamentos.excluir(mercado.id)
    assert saldo(servicos, conta.id) == Decimal("1350.00")
    (_, situacao), = servicos.orcamentos.acompanhar(mes)
    assert situacao.consumido == Decimal("0.00") and not situacao.ultrapassado

    resumo = servicos.relatorios.resumo_mensal(mes)
    assert (resumo.total_receitas, resumo.total_despesas, resumo.resultado) == (
        Decimal("1500.00"), Decimal("150.00"), Decimal("1350.00"),
    )


# ================================================================ contas
def test_editar_conta_recalcula_saldo(servicos, base):
    conta, salario, *_ = base
    servicos.lancamentos.registrar("receita", "Salário", "100", hoje(), conta.id, salario.id)
    servicos.contas.editar(conta.id, "Conta Principal", "50,00")
    assert saldo(servicos, conta.id) == Decimal("150.00")


def test_nao_exclui_conta_com_lancamentos(servicos, base):
    conta, salario, *_ = base
    servicos.lancamentos.registrar("receita", "Salário", "100", hoje(), conta.id, salario.id)
    with pytest.raises(ExclusaoNaoPermitidaError):
        servicos.contas.excluir(conta.id)


def test_exclui_conta_sem_lancamentos(servicos, base):
    conta, *_ = base
    servicos.contas.excluir(conta.id)
    assert servicos.contas.listar() == []


def test_conta_com_nome_repetido(servicos, base):
    with pytest.raises(RegistroDuplicadoError):
        servicos.contas.criar("conta corrente", "0")


# ============================================================ categorias
def test_nao_exclui_categoria_em_uso(servicos, base):
    conta, _, alimentacao, _ = base
    servicos.lancamentos.registrar("despesa", "Mercado", "10", hoje(), conta.id, alimentacao.id)
    with pytest.raises(ExclusaoNaoPermitidaError):
        servicos.categorias.excluir(alimentacao.id)


def test_nao_muda_tipo_de_categoria_em_uso(servicos, base):
    conta, _, alimentacao, _ = base
    servicos.orcamentos.definir(alimentacao.id, Competencia.atual(), "100")
    with pytest.raises(ExclusaoNaoPermitidaError):
        servicos.categorias.editar(alimentacao.id, "Alimentação", "receita")
    servicos.categorias.editar(alimentacao.id, "Comida", "despesa")  # renomear é permitido
    assert servicos.categorias.listar("despesa")[0].nome == "Comida"


def test_exclui_e_muda_tipo_de_categoria_livre(servicos, base):
    *_, transporte = base
    servicos.categorias.editar(transporte.id, "Reembolso", "receita")
    assert [c.nome for c in servicos.categorias.listar(TipoLancamento.RECEITA)] == ["Reembolso", "Salário"]
    servicos.categorias.excluir(transporte.id)
    with pytest.raises(RegistroNaoEncontradoError):
        servicos.categorias.excluir(transporte.id)


# =========================================================== lançamentos
def test_registrar_cria_subclasse_correta(servicos, base):
    conta, salario, *_ = base
    lancamento = servicos.lancamentos.registrar("receita", "Salário", "10", hoje(), conta.id, salario.id)
    assert isinstance(servicos.lancamentos.obter(lancamento.id), Receita)


def test_categoria_incompativel_no_servico(servicos, base):
    conta, salario, *_ = base
    with pytest.raises(CategoriaIncompativelError):
        servicos.lancamentos.registrar("despesa", "Erro", "10", hoje(), conta.id, salario.id)


def test_reenvio_do_formulario_nao_duplica(servicos, base):
    conta, salario, *_ = base
    chave = uuid4()
    primeiro = servicos.lancamentos.registrar("receita", "Salário", "10", hoje(), conta.id, salario.id, chave)
    segundo = servicos.lancamentos.registrar("receita", "Salário", "10", hoje(), conta.id, salario.id, chave)
    assert primeiro.id == segundo.id
    assert len(servicos.lancamentos.consultar()) == 1


def test_filtros(servicos, base):
    conta, salario, alimentacao, transporte = base
    carteira = servicos.contas.criar("Carteira", "0")
    servicos.lancamentos.registrar("receita", "Salário", "1000", hoje(), conta.id, salario.id)
    servicos.lancamentos.registrar("despesa", "Mercado", "50", hoje(), carteira.id, alimentacao.id)
    servicos.lancamentos.registrar("despesa", "Ônibus", "5", hoje(), conta.id, transporte.id)
    consultar = servicos.lancamentos.consultar
    assert len(consultar(FiltroLancamentos(tipo=TipoLancamento.DESPESA))) == 2
    assert len(consultar(FiltroLancamentos(conta_id=carteira.id))) == 1
    assert len(consultar(FiltroLancamentos(categoria_id=transporte.id))) == 1
    assert len(consultar(FiltroLancamentos(data_inicio=hoje(), data_fim=hoje()))) == 3


def test_excluir_lancamento_inexistente(servicos):
    with pytest.raises(RegistroNaoEncontradoError):
        servicos.lancamentos.excluir(999)


# ============================================================ orçamentos
def test_orcamento_unico_por_categoria_e_mes(servicos, base):
    *_, alimentacao, _ = base
    servicos.orcamentos.definir(alimentacao.id, Competencia(2026, 1), "100")
    with pytest.raises(RegistroDuplicadoError):
        servicos.orcamentos.definir(alimentacao.id, Competencia(2026, 1), "200")
    servicos.orcamentos.definir(alimentacao.id, Competencia(2026, 2), "200")  # outro mês: permitido


def test_orcamento_de_receita_e_recusado(servicos, base):
    _, salario, *_ = base
    with pytest.raises(CategoriaIncompativelError):
        servicos.orcamentos.definir(salario.id, Competencia.atual(), "100")


def test_alterar_limite_e_excluir_orcamento(servicos, base):
    conta, _, alimentacao, _ = base
    mes = Competencia.atual()
    servicos.lancamentos.registrar("despesa", "Mercado", "300", hoje(), conta.id, alimentacao.id)
    orcamento = servicos.orcamentos.definir(alimentacao.id, mes, "250")
    servicos.orcamentos.alterar_limite(orcamento.id, "400")
    (_, situacao), = servicos.orcamentos.acompanhar(mes)
    assert not situacao.ultrapassado
    servicos.orcamentos.excluir(orcamento.id)
    assert servicos.orcamentos.acompanhar(mes) == []


def test_painel_separa_saldo_acumulado_de_resultado_mensal(servicos, base):
    conta, salario, alimentacao, _ = base
    servicos.contas.editar(conta.id, conta.nome, "1.000,00")
    servicos.lancamentos.registrar("receita", "Salário", "500", hoje(), conta.id, salario.id)
    servicos.lancamentos.registrar("despesa", "Mercado", "200", hoje(), conta.id, alimentacao.id)
    painel = servicos.relatorios.painel(Competencia.atual())
    assert painel.saldo_total == Decimal("1300.00")  # acumulado (inclui saldo inicial)
    assert painel.resumo.resultado == Decimal("300.00")  # só o mês
    assert len(painel.ultimos_lancamentos) == 2
