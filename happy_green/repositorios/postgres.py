"""Repositórios PostgreSQL (Supabase) com Psycopg 3.

Regras seguidas aqui:
- Todo SQL é parametrizado (``%s``): valores nunca são concatenados no texto
  do comando, o que impede injeção de SQL.
- Cada operação usa uma conexão emprestada do pool dentro de um bloco
  ``with``: se tudo der certo, a transação é confirmada (commit); se ocorrer
  erro, é desfeita (rollback).
- Ao ler do banco, os registros são convertidos de volta em objetos de
  domínio. Lançamentos voltam como ``Receita`` ou ``Despesa`` (pela fábrica
  ``criar_lancamento``), preservando o polimorfismo.
- Erros do banco viram exceções de domínio com mensagens compreensíveis; o
  detalhe técnico vai para o log.
"""

import logging
from contextlib import contextmanager
from uuid import UUID

import psycopg
from psycopg import errors
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

from happy_green.dominio import (
    Categoria,
    Competencia,
    ContaFinanceira,
    Lancamento,
    OrcamentoMensal,
    TipoLancamento,
    criar_lancamento,
)
from happy_green.excecoes import (
    DadosInvalidosError,
    ErroInfraestrutura,
    ExclusaoNaoPermitidaError,
    RegistroDuplicadoError,
    RegistroNaoEncontradoError,
)
from happy_green.repositorios.base import (
    FiltroLancamentos,
    RepositorioCategorias,
    RepositorioContas,
    RepositorioLancamentos,
    RepositorioOrcamentos,
)

log = logging.getLogger("happy_green.repositorios")

# Restrição do banco -> mensagem para o usuário
MENSAGENS_RESTRICOES = {
    "contas_nome_unico": "Já existe uma conta com esse nome.",
    "categorias_nome_tipo_unico": "Já existe uma categoria com esse nome e tipo.",
    "orcamentos_categoria_competencia_unico": "Já existe um orçamento para essa categoria nesse mês.",
    "lancamentos_conta_fk": "A conta possui lançamentos ou não existe mais.",
    "lancamentos_categoria_fk": "A categoria está em uso, não existe mais ou é de outro tipo.",
    "orcamentos_categoria_fk": "A categoria está em uso por orçamentos ou não é de despesa.",
}


class RepositorioPostgres:
    """Superclasse com o acesso ao pool e a tradução de erros."""

    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    @contextmanager
    def _conexao(self):
        """Empresta uma conexão do pool e traduz os erros do banco."""
        try:
            with self._pool.connection() as conexao:
                conexao.row_factory = dict_row
                yield conexao
        except errors.UniqueViolation as erro:
            raise RegistroDuplicadoError(self._mensagem(erro, "Registro duplicado.")) from erro
        except errors.ForeignKeyViolation as erro:
            raise ExclusaoNaoPermitidaError(
                self._mensagem(erro, "Operação deixaria referências inválidas.")
            ) from erro
        except (errors.CheckViolation, errors.NotNullViolation, errors.StringDataRightTruncation) as erro:
            raise DadosInvalidosError("Os dados informados violam uma regra do banco de dados.") from erro
        except (psycopg.OperationalError, PoolTimeout) as erro:
            log.exception("Falha de conexão com o banco de dados")
            raise ErroInfraestrutura(
                "Não foi possível acessar o banco de dados agora. Tente novamente em instantes."
            ) from erro
        except psycopg.Error as erro:
            log.exception("Erro inesperado no banco de dados")
            raise ErroInfraestrutura("Ocorreu um erro inesperado ao acessar o banco de dados.") from erro

    @staticmethod
    def _mensagem(erro: psycopg.Error, padrao: str) -> str:
        restricao = getattr(erro.diag, "constraint_name", None)
        return MENSAGENS_RESTRICOES.get(restricao, padrao)

    @staticmethod
    def _exigir_linha_afetada(cursor, descricao: str) -> None:
        if cursor.rowcount == 0:
            raise RegistroNaoEncontradoError(f"{descricao} não encontrado(a). Ele(a) pode ter sido excluído(a).")


# ================================================================== contas
def _montar_conta(linha: dict, prefixo: str = "") -> ContaFinanceira:
    return ContaFinanceira(
        nome=linha[f"{prefixo}nome"],
        saldo_inicial=linha[f"{prefixo}saldo_inicial"],
        id=linha[f"{prefixo}id"],
    )


class ContasPostgres(RepositorioPostgres, RepositorioContas):
    def listar(self) -> list[ContaFinanceira]:
        with self._conexao() as conexao:
            linhas = conexao.execute("SELECT id, nome, saldo_inicial FROM contas ORDER BY lower(nome)").fetchall()
        return [_montar_conta(linha) for linha in linhas]

    def obter(self, id: int) -> ContaFinanceira:
        with self._conexao() as conexao:
            linha = conexao.execute("SELECT id, nome, saldo_inicial FROM contas WHERE id = %s", (id,)).fetchone()
        if linha is None:
            raise RegistroNaoEncontradoError("Conta não encontrada. Ela pode ter sido excluída.")
        return _montar_conta(linha)

    def adicionar(self, conta: ContaFinanceira) -> ContaFinanceira:
        with self._conexao() as conexao:
            linha = conexao.execute(
                "INSERT INTO contas (nome, saldo_inicial) VALUES (%s, %s) RETURNING id",
                (conta.nome, conta.saldo_inicial),
            ).fetchone()
        conta.atribuir_id(linha["id"])
        return conta

    def atualizar(self, conta: ContaFinanceira) -> None:
        with self._conexao() as conexao:
            cursor = conexao.execute(
                "UPDATE contas SET nome = %s, saldo_inicial = %s WHERE id = %s",
                (conta.nome, conta.saldo_inicial, conta.id),
            )
            self._exigir_linha_afetada(cursor, "Conta")

    def remover(self, id: int) -> None:
        with self._conexao() as conexao:
            cursor = conexao.execute("DELETE FROM contas WHERE id = %s", (id,))
            self._exigir_linha_afetada(cursor, "Conta")


# ============================================================== categorias
def _montar_categoria(linha: dict, prefixo: str = "") -> Categoria:
    return Categoria(nome=linha[f"{prefixo}nome"], tipo=linha[f"{prefixo}tipo"], id=linha[f"{prefixo}id"])


class CategoriasPostgres(RepositorioPostgres, RepositorioCategorias):
    def listar(self, tipo: TipoLancamento | None = None) -> list[Categoria]:
        with self._conexao() as conexao:
            if tipo is None:
                linhas = conexao.execute("SELECT id, nome, tipo FROM categorias ORDER BY tipo, lower(nome)").fetchall()
            else:
                linhas = conexao.execute(
                    "SELECT id, nome, tipo FROM categorias WHERE tipo = %s ORDER BY lower(nome)", (tipo.value,)
                ).fetchall()
        return [_montar_categoria(linha) for linha in linhas]

    def obter(self, id: int) -> Categoria:
        with self._conexao() as conexao:
            linha = conexao.execute("SELECT id, nome, tipo FROM categorias WHERE id = %s", (id,)).fetchone()
        if linha is None:
            raise RegistroNaoEncontradoError("Categoria não encontrada. Ela pode ter sido excluída.")
        return _montar_categoria(linha)

    def adicionar(self, categoria: Categoria) -> Categoria:
        with self._conexao() as conexao:
            linha = conexao.execute(
                "INSERT INTO categorias (nome, tipo) VALUES (%s, %s) RETURNING id",
                (categoria.nome, categoria.tipo.value),
            ).fetchone()
        categoria.atribuir_id(linha["id"])
        return categoria

    def atualizar(self, categoria: Categoria) -> None:
        with self._conexao() as conexao:
            cursor = conexao.execute(
                "UPDATE categorias SET nome = %s, tipo = %s WHERE id = %s",
                (categoria.nome, categoria.tipo.value, categoria.id),
            )
            self._exigir_linha_afetada(cursor, "Categoria")

    def remover(self, id: int) -> None:
        with self._conexao() as conexao:
            cursor = conexao.execute("DELETE FROM categorias WHERE id = %s", (id,))
            self._exigir_linha_afetada(cursor, "Categoria")

    def em_uso(self, id: int) -> bool:
        with self._conexao() as conexao:
            linha = conexao.execute(
                """
                SELECT EXISTS (SELECT 1 FROM lancamentos WHERE categoria_id = %(id)s)
                    OR EXISTS (SELECT 1 FROM orcamentos WHERE categoria_id = %(id)s) AS em_uso
                """,
                {"id": id},
            ).fetchone()
        return linha["em_uso"]


# ============================================================= lançamentos
_SELECT_LANCAMENTOS = """
    SELECT l.id, l.tipo, l.descricao, l.valor, l.data,
           c.id AS conta_id, c.nome AS conta_nome, c.saldo_inicial AS conta_saldo_inicial,
           k.id AS categoria_id, k.nome AS categoria_nome, k.tipo AS categoria_tipo
      FROM lancamentos l
      JOIN contas c ON c.id = l.conta_id
      JOIN categorias k ON k.id = l.categoria_id
"""


def _montar_lancamento(linha: dict) -> Lancamento:
    """Reconstrói Receita ou Despesa a partir da coluna ``tipo``."""
    return criar_lancamento(
        linha["tipo"],
        descricao=linha["descricao"],
        valor=linha["valor"],  # o psycopg devolve NUMERIC como Decimal
        data=linha["data"],
        conta=_montar_conta(linha, "conta_"),
        categoria=_montar_categoria(linha, "categoria_"),
        id=linha["id"],
    )


class LancamentosPostgres(RepositorioPostgres, RepositorioLancamentos):
    def listar(self, filtro: FiltroLancamentos | None = None) -> list[Lancamento]:
        filtro = filtro or FiltroLancamentos()
        condicoes, parametros = [], []
        # Só os critérios preenchidos entram no WHERE; os valores vão como parâmetros.
        if filtro.data_inicio:
            condicoes.append("l.data >= %s")
            parametros.append(filtro.data_inicio)
        if filtro.data_fim:
            condicoes.append("l.data <= %s")
            parametros.append(filtro.data_fim)
        if filtro.conta_id:
            condicoes.append("l.conta_id = %s")
            parametros.append(filtro.conta_id)
        if filtro.categoria_id:
            condicoes.append("l.categoria_id = %s")
            parametros.append(filtro.categoria_id)
        if filtro.tipo:
            condicoes.append("l.tipo = %s")
            parametros.append(filtro.tipo.value)
        where = f" WHERE {' AND '.join(condicoes)}" if condicoes else ""
        with self._conexao() as conexao:
            linhas = conexao.execute(f"{_SELECT_LANCAMENTOS}{where} ORDER BY l.data DESC, l.id DESC", parametros).fetchall()
        return [_montar_lancamento(linha) for linha in linhas]

    def obter(self, id: int) -> Lancamento:
        with self._conexao() as conexao:
            linha = conexao.execute(f"{_SELECT_LANCAMENTOS} WHERE l.id = %s", (id,)).fetchone()
        if linha is None:
            raise RegistroNaoEncontradoError("Lançamento não encontrado. Ele pode ter sido excluído.")
        return _montar_lancamento(linha)

    def adicionar(self, lancamento: Lancamento, chave_envio: UUID | None = None) -> Lancamento:
        with self._conexao() as conexao:
            linha = conexao.execute(
                """
                INSERT INTO lancamentos (tipo, descricao, valor, data, conta_id, categoria_id, chave_envio)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chave_envio) DO NOTHING
                RETURNING id
                """,
                (
                    lancamento.tipo.value,
                    lancamento.descricao,
                    lancamento.valor,
                    lancamento.data,
                    lancamento.conta.id,
                    lancamento.categoria.id,
                    chave_envio,
                ),
            ).fetchone()
            if linha is None:  # mesma chave de envio: o formulário já tinha sido gravado
                existente = conexao.execute(
                    "SELECT id FROM lancamentos WHERE chave_envio = %s", (chave_envio,)
                ).fetchone()
                log.info("Reenvio de formulário ignorado (lançamento %s já gravado)", existente["id"])
                return self.obter(existente["id"])
        lancamento.atribuir_id(linha["id"])
        return lancamento

    def atualizar(self, lancamento: Lancamento) -> None:
        with self._conexao() as conexao:
            cursor = conexao.execute(
                """
                UPDATE lancamentos
                   SET descricao = %s, valor = %s, data = %s, conta_id = %s, categoria_id = %s
                 WHERE id = %s AND tipo = %s
                """,
                (
                    lancamento.descricao,
                    lancamento.valor,
                    lancamento.data,
                    lancamento.conta.id,
                    lancamento.categoria.id,
                    lancamento.id,
                    lancamento.tipo.value,
                ),
            )
            self._exigir_linha_afetada(cursor, "Lançamento")

    def remover(self, id: int) -> None:
        with self._conexao() as conexao:
            cursor = conexao.execute("DELETE FROM lancamentos WHERE id = %s", (id,))
            self._exigir_linha_afetada(cursor, "Lançamento")

    def existe_para_conta(self, conta_id: int) -> bool:
        with self._conexao() as conexao:
            linha = conexao.execute(
                "SELECT EXISTS (SELECT 1 FROM lancamentos WHERE conta_id = %s) AS existe", (conta_id,)
            ).fetchone()
        return linha["existe"]


# ============================================================== orçamentos
_SELECT_ORCAMENTOS = """
    SELECT o.id, o.competencia, o.limite,
           k.id AS categoria_id, k.nome AS categoria_nome, k.tipo AS categoria_tipo
      FROM orcamentos o
      JOIN categorias k ON k.id = o.categoria_id
"""


def _montar_orcamento(linha: dict) -> OrcamentoMensal:
    return OrcamentoMensal(
        categoria=_montar_categoria(linha, "categoria_"),
        competencia=Competencia.de_data(linha["competencia"]),
        limite=linha["limite"],
        id=linha["id"],
    )


class OrcamentosPostgres(RepositorioPostgres, RepositorioOrcamentos):
    def listar(self, competencia: Competencia | None = None) -> list[OrcamentoMensal]:
        with self._conexao() as conexao:
            if competencia is None:
                linhas = conexao.execute(f"{_SELECT_ORCAMENTOS} ORDER BY o.competencia DESC, lower(k.nome)").fetchall()
            else:
                linhas = conexao.execute(
                    f"{_SELECT_ORCAMENTOS} WHERE o.competencia = %s ORDER BY lower(k.nome)",
                    (competencia.primeiro_dia,),
                ).fetchall()
        return [_montar_orcamento(linha) for linha in linhas]

    def obter(self, id: int) -> OrcamentoMensal:
        with self._conexao() as conexao:
            linha = conexao.execute(f"{_SELECT_ORCAMENTOS} WHERE o.id = %s", (id,)).fetchone()
        if linha is None:
            raise RegistroNaoEncontradoError("Orçamento não encontrado. Ele pode ter sido excluído.")
        return _montar_orcamento(linha)

    def adicionar(self, orcamento: OrcamentoMensal) -> OrcamentoMensal:
        with self._conexao() as conexao:
            linha = conexao.execute(
                "INSERT INTO orcamentos (categoria_id, competencia, limite) VALUES (%s, %s, %s) RETURNING id",
                (orcamento.categoria.id, orcamento.competencia.primeiro_dia, orcamento.limite),
            ).fetchone()
        orcamento.atribuir_id(linha["id"])
        return orcamento

    def atualizar(self, orcamento: OrcamentoMensal) -> None:
        with self._conexao() as conexao:
            cursor = conexao.execute(
                "UPDATE orcamentos SET limite = %s WHERE id = %s", (orcamento.limite, orcamento.id)
            )
            self._exigir_linha_afetada(cursor, "Orçamento")

    def remover(self, id: int) -> None:
        with self._conexao() as conexao:
            cursor = conexao.execute("DELETE FROM orcamentos WHERE id = %s", (id,))
            self._exigir_linha_afetada(cursor, "Orçamento")

    def existe(self, categoria_id: int, competencia: Competencia) -> bool:
        with self._conexao() as conexao:
            linha = conexao.execute(
                "SELECT EXISTS (SELECT 1 FROM orcamentos WHERE categoria_id = %s AND competencia = %s) AS existe",
                (categoria_id, competencia.primeiro_dia),
            ).fetchone()
        return linha["existe"]


def montar_repositorios_postgres(pool: ConnectionPool):
    """Cria os quatro repositórios compartilhando o mesmo pool."""
    return (
        ContasPostgres(pool),
        CategoriasPostgres(pool),
        LancamentosPostgres(pool),
        OrcamentosPostgres(pool),
    )
