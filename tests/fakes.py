"""Repositórios em memória usados SOMENTE nos testes de serviço.

Eles cumprem os mesmos contratos de ``happy_green.repositorios.base`` e
imitam as regras do banco (ids, unicidade, chaves estrangeiras). Guardam e
devolvem cópias, como acontece com dados lidos de um banco de verdade.
"""

import copy
from itertools import count

from happy_green.dominio import Competencia, TipoLancamento
from happy_green.excecoes import ExclusaoNaoPermitidaError, RegistroDuplicadoError, RegistroNaoEncontradoError
from happy_green.repositorios.base import (
    FiltroLancamentos,
    RepositorioCategorias,
    RepositorioContas,
    RepositorioLancamentos,
    RepositorioOrcamentos,
)


class BancoEmMemoria:
    def __init__(self) -> None:
        self.contas: dict = {}
        self.categorias: dict = {}
        self.lancamentos: dict = {}
        self.orcamentos: dict = {}
        self.chaves_envio: dict = {}
        self._ids = count(1)

    def proximo_id(self) -> int:
        return next(self._ids)


class _Base:
    tabela = ""
    nome = "registro"

    def __init__(self, banco: BancoEmMemoria) -> None:
        self.banco = banco

    @property
    def _dados(self) -> dict:
        return getattr(self.banco, self.tabela)

    def obter(self, id):
        if id not in self._dados:
            raise RegistroNaoEncontradoError(f"{self.nome.capitalize()} não encontrado(a).")
        return copy.deepcopy(self._dados[id])

    def _inserir(self, objeto):
        objeto.atribuir_id(self.banco.proximo_id())
        self._dados[objeto.id] = copy.deepcopy(objeto)
        return objeto

    def atualizar(self, objeto) -> None:
        self.obter(objeto.id)
        self._dados[objeto.id] = copy.deepcopy(objeto)

    def remover(self, id) -> None:
        self.obter(id)
        del self._dados[id]


class ContasEmMemoria(_Base, RepositorioContas):
    tabela, nome = "contas", "conta"

    def listar(self):
        return sorted((copy.deepcopy(c) for c in self._dados.values()), key=lambda c: c.nome.lower())

    def adicionar(self, conta):
        if any(c.nome.lower() == conta.nome.lower() for c in self._dados.values()):
            raise RegistroDuplicadoError("Já existe uma conta com esse nome.")
        return self._inserir(conta)

    def remover(self, id):
        if any(l.conta.id == id for l in self.banco.lancamentos.values()):
            raise ExclusaoNaoPermitidaError("Conta com lançamentos.")  # imita a FK do banco
        super().remover(id)


class CategoriasEmMemoria(_Base, RepositorioCategorias):
    tabela, nome = "categorias", "categoria"

    def listar(self, tipo=None):
        itens = (copy.deepcopy(c) for c in self._dados.values() if tipo is None or c.tipo is tipo)
        return sorted(itens, key=lambda c: (c.tipo.value, c.nome.lower()))

    def adicionar(self, categoria):
        if any(c.nome.lower() == categoria.nome.lower() and c.tipo is categoria.tipo for c in self._dados.values()):
            raise RegistroDuplicadoError("Já existe uma categoria com esse nome e tipo.")
        return self._inserir(categoria)

    def em_uso(self, id):
        return any(l.categoria.id == id for l in self.banco.lancamentos.values()) or any(
            o.categoria.id == id for o in self.banco.orcamentos.values()
        )


class LancamentosEmMemoria(_Base, RepositorioLancamentos):
    tabela, nome = "lancamentos", "lançamento"

    def listar(self, filtro: FiltroLancamentos | None = None):
        filtro = filtro or FiltroLancamentos()
        itens = [copy.deepcopy(l) for l in self._dados.values() if filtro.aceita(l)]
        return sorted(itens, key=lambda l: (l.data, l.id), reverse=True)

    def adicionar(self, lancamento, chave_envio=None):
        if chave_envio is not None and chave_envio in self.banco.chaves_envio:
            return self.obter(self.banco.chaves_envio[chave_envio])  # reenvio: não duplica
        criado = self._inserir(lancamento)
        if chave_envio is not None:
            self.banco.chaves_envio[chave_envio] = criado.id
        return criado

    def existe_para_conta(self, conta_id):
        return any(l.conta.id == conta_id for l in self._dados.values())


class OrcamentosEmMemoria(_Base, RepositorioOrcamentos):
    tabela, nome = "orcamentos", "orçamento"

    def listar(self, competencia: Competencia | None = None):
        itens = (copy.deepcopy(o) for o in self._dados.values() if competencia is None or o.competencia == competencia)
        return sorted(itens, key=lambda o: (o.competencia, o.categoria.nome))

    def adicionar(self, orcamento):
        if self.existe(orcamento.categoria.id, orcamento.competencia):
            raise RegistroDuplicadoError("Orçamento duplicado.")
        return self._inserir(orcamento)

    def existe(self, categoria_id, competencia):
        return any(o.categoria.id == categoria_id and o.competencia == competencia for o in self._dados.values())


def criar_repositorios_em_memoria():
    banco = BancoEmMemoria()
    return (
        ContasEmMemoria(banco),
        CategoriasEmMemoria(banco),
        LancamentosEmMemoria(banco),
        OrcamentosEmMemoria(banco),
    )


__all__ = ["TipoLancamento", "criar_repositorios_em_memoria"]
