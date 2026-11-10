"""Testes de integração com o PostgreSQL do Supabase.

Usam o schema SEPARADO ``happy_green_teste`` (seção ``[banco_teste]`` de
``.streamlit/secrets.toml``); os dados da demonstração não são tocados.
São ignorados automaticamente quando essa configuração não existe.

Executar: ``pytest -m integracao -v``
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from happy_green.config import ConfiguracaoBanco, criar_pool, ler_configuracao_arquivo
from happy_green.dominio import Competencia, Despesa, Receita, hoje
from happy_green.excecoes import (
    CategoriaIncompativelError,
    ErroHappyGreen,
    ExclusaoNaoPermitidaError,
    RegistroDuplicadoError,
)
from happy_green.repositorios.postgres import montar_repositorios_postgres
from happy_green.servicos import montar_servicos

pytestmark = pytest.mark.integracao


@pytest.fixture(scope="module")
def config() -> ConfiguracaoBanco:
    try:
        configuracao = ler_configuracao_arquivo(secao="banco_teste")
    except ErroHappyGreen as erro:
        pytest.skip(f"Banco de testes não configurado: {erro}")
    assert configuracao.schema == "happy_green_teste", "Os testes nunca devem usar o schema da demonstração."
    return configuracao


@pytest.fixture
def pool(config):
    pool = criar_pool(config, tamanho_maximo=2)
    with pool.connection() as conexao:  # começa cada teste com o schema de testes vazio
        conexao.execute("TRUNCATE lancamentos, orcamentos, contas, categorias")
    yield pool
    pool.close()


def nova_aplicacao(pool):
    return montar_servicos(*montar_repositorios_postgres(pool))


def saldo(servicos, conta_id):
    return dict((c.id, s) for c, s in servicos.contas.listar_com_saldo())[conta_id]


def test_cenario_completo_com_persistencia_e_reinicio(config, pool):
    servicos = nova_aplicacao(pool)
    dia, mes = hoje(), Competencia.atual()

    conta = servicos.contas.criar("Conta Cenário", "0")
    salario = servicos.categorias.criar("Salário", "receita")
    alimentacao = servicos.categorias.criar("Alimentação", "despesa")
    transporte = servicos.categorias.criar("Transporte", "despesa")

    servicos.lancamentos.registrar("receita", "Salário", "1.500,00", dia, conta.id, salario.id)
    mercado = servicos.lancamentos.registrar("despesa", "Mercado", "300,00", dia, conta.id, alimentacao.id)
    onibus = servicos.lancamentos.registrar("despesa", "Ônibus", "120,00", dia, conta.id, transporte.id)
    assert saldo(servicos, conta.id) == Decimal("1080.00")

    servicos.orcamentos.definir(alimentacao.id, mes, "250,00")
    (_, situacao), = servicos.orcamentos.acompanhar(mes)
    assert situacao.ultrapassado and situacao.excedente == Decimal("50.00")

    servicos.lancamentos.editar(onibus.id, "Ônibus", "150,00", dia, conta.id, transporte.id)
    assert saldo(servicos, conta.id) == Decimal("1050.00")

    servicos.lancamentos.excluir(mercado.id)
    assert saldo(servicos, conta.id) == Decimal("1350.00")
    (_, situacao), = servicos.orcamentos.acompanhar(mes)
    assert situacao.consumido == Decimal("0.00") and not situacao.ultrapassado

    # "Reinício da aplicação": fecha todas as conexões e cria um pool novo,
    # como acontece quando o servidor do Streamlit reinicia.
    pool.close()
    novo_pool = criar_pool(config, tamanho_maximo=2)
    try:
        reiniciada = nova_aplicacao(novo_pool)
        assert saldo(reiniciada, conta.id) == Decimal("1350.00")
        lancamentos = reiniciada.lancamentos.consultar()
        assert sorted(type(l).__name__ for l in lancamentos) == ["Despesa", "Receita"]
        assert {l.descricao: l.valor for l in lancamentos} == {
            "Salário": Decimal("1500.00"),
            "Ônibus": Decimal("150.00"),
        }
    finally:
        novo_pool.close()


def test_reconstroi_subclasses_e_decimal(pool):
    servicos = nova_aplicacao(pool)
    conta = servicos.contas.criar("Carteira", "10,05")
    salario = servicos.categorias.criar("Salário", "receita")
    mercado = servicos.categorias.criar("Mercado", "despesa")
    r = servicos.lancamentos.registrar("receita", "Pix", "0,10", hoje(), conta.id, salario.id)
    d = servicos.lancamentos.registrar("despesa", "Pão", "0,20", hoje(), conta.id, mercado.id)
    assert isinstance(servicos.lancamentos.obter(r.id), Receita)
    assert isinstance(servicos.lancamentos.obter(d.id), Despesa)
    lido = servicos.lancamentos.obter(r.id).valor
    assert isinstance(lido, Decimal) and lido == Decimal("0.10")
    assert saldo(servicos, conta.id) == Decimal("9.95")  # 10,05 + 0,10 - 0,20 sem erro de float


def test_restricoes_do_banco(pool):
    servicos = nova_aplicacao(pool)
    conta = servicos.contas.criar("Conta", "0")
    salario = servicos.categorias.criar("Salário", "receita")
    alimentacao = servicos.categorias.criar("Alimentação", "despesa")
    servicos.lancamentos.registrar("despesa", "Mercado", "10", hoje(), conta.id, alimentacao.id)

    with pytest.raises(RegistroDuplicadoError):
        servicos.contas.criar("CONTA", "0")  # nome único sem diferenciar maiúsculas
    with pytest.raises(ExclusaoNaoPermitidaError):
        servicos.contas.excluir(conta.id)
    with pytest.raises(ExclusaoNaoPermitidaError):
        servicos.categorias.excluir(alimentacao.id)
    with pytest.raises(CategoriaIncompativelError):
        servicos.orcamentos.definir(salario.id, Competencia.atual(), "100")
    servicos.orcamentos.definir(alimentacao.id, Competencia.atual(), "100")
    with pytest.raises(RegistroDuplicadoError):
        servicos.orcamentos.definir(alimentacao.id, Competencia.atual(), "200")


def test_banco_recusa_dados_invalidos_mesmo_sem_o_dominio(pool):
    """Defesa em profundidade: o banco também protege as regras."""
    import psycopg

    servicos = nova_aplicacao(pool)
    conta = servicos.contas.criar("Conta", "0")
    salario = servicos.categorias.criar("Salário", "receita")
    with pool.connection() as conexao:
        with pytest.raises(psycopg.errors.CheckViolation):
            conexao.execute(
                "INSERT INTO lancamentos (tipo, descricao, valor, data, conta_id, categoria_id) "
                "VALUES ('receita', 'x', -5, current_date, %s, %s)",
                (conta.id, salario.id),
            )
    with pool.connection() as conexao:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):  # categoria de receita em despesa
            conexao.execute(
                "INSERT INTO lancamentos (tipo, descricao, valor, data, conta_id, categoria_id) "
                "VALUES ('despesa', 'x', 5, current_date, %s, %s)",
                (conta.id, salario.id),
            )


def test_reenvio_nao_duplica_no_banco(pool):
    servicos = nova_aplicacao(pool)
    conta = servicos.contas.criar("Conta", "0")
    salario = servicos.categorias.criar("Salário", "receita")
    chave = uuid4()
    a = servicos.lancamentos.registrar("receita", "Salário", "10", hoje(), conta.id, salario.id, chave)
    b = servicos.lancamentos.registrar("receita", "Salário", "10", hoje(), conta.id, salario.id, chave)
    assert a.id == b.id
    assert len(servicos.lancamentos.consultar()) == 1


def test_conexao_criptografada(pool):
    with pool.connection() as conexao:
        assert conexao.pgconn.ssl_in_use
        schema = conexao.execute("SELECT current_schema()").fetchone()[0]
    assert schema == "happy_green_teste"
