"""Serviços: coordenam os casos de uso entre domínio e repositórios.

Os serviços não conhecem Streamlit nem SQL. Eles recebem dados simples da
interface (textos, ids, datas), buscam os objetos nos repositórios, pedem
ao domínio para validar e calcular, e mandam gravar o resultado.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from happy_green.dominio import (
    Categoria,
    Competencia,
    ContaFinanceira,
    Lancamento,
    OrcamentoMensal,
    ResumoMensal,
    SituacaoOrcamento,
    TipoLancamento,
    criar_lancamento,
)
from happy_green.dominio.dinheiro import ZERO
from happy_green.excecoes import ExclusaoNaoPermitidaError, RegistroDuplicadoError
from happy_green.repositorios.base import (
    FiltroLancamentos,
    RepositorioCategorias,
    RepositorioContas,
    RepositorioLancamentos,
    RepositorioOrcamentos,
)


# ================================================================== contas
class ServicoContas:
    def __init__(self, contas: RepositorioContas, lancamentos: RepositorioLancamentos) -> None:
        self._contas = contas
        self._lancamentos = lancamentos

    def listar(self) -> list[ContaFinanceira]:
        return self._contas.listar()

    def listar_com_saldo(self) -> list[tuple[ContaFinanceira, Decimal]]:
        lancamentos = self._lancamentos.listar()
        return [(conta, conta.calcular_saldo(lancamentos)) for conta in self._contas.listar()]

    def criar(self, nome: str, saldo_inicial: str | Decimal) -> ContaFinanceira:
        return self._contas.adicionar(ContaFinanceira(nome, saldo_inicial))

    def editar(self, id: int, nome: str, saldo_inicial: str | Decimal) -> ContaFinanceira:
        conta = self._contas.obter(id)
        conta.nome = nome
        conta.saldo_inicial = saldo_inicial
        self._contas.atualizar(conta)
        return conta

    def excluir(self, id: int) -> None:
        conta = self._contas.obter(id)
        if self._lancamentos.existe_para_conta(id):
            raise ExclusaoNaoPermitidaError(
                f"A conta '{conta.nome}' possui lançamentos. Exclua ou mova os lançamentos antes."
            )
        self._contas.remover(id)


# ============================================================== categorias
class ServicoCategorias:
    def __init__(self, categorias: RepositorioCategorias) -> None:
        self._categorias = categorias

    def listar(self, tipo: TipoLancamento | str | None = None) -> list[Categoria]:
        return self._categorias.listar(TipoLancamento.converter(tipo) if tipo else None)

    def criar(self, nome: str, tipo: TipoLancamento | str) -> Categoria:
        return self._categorias.adicionar(Categoria(nome, tipo))

    def editar(self, id: int, nome: str, tipo: TipoLancamento | str) -> Categoria:
        categoria = self._categorias.obter(id)
        novo_tipo = TipoLancamento.converter(tipo)
        if novo_tipo is not categoria.tipo and self._categorias.em_uso(id):
            raise ExclusaoNaoPermitidaError(
                f"A categoria '{categoria.nome}' já é usada em lançamentos ou orçamentos; o tipo não pode mudar."
            )
        categoria.nome = nome
        categoria.alterar_tipo(novo_tipo)
        self._categorias.atualizar(categoria)
        return categoria

    def excluir(self, id: int) -> None:
        categoria = self._categorias.obter(id)
        if self._categorias.em_uso(id):
            raise ExclusaoNaoPermitidaError(
                f"A categoria '{categoria.nome}' está em uso por lançamentos ou orçamentos e não pode ser excluída."
            )
        self._categorias.remover(id)


# ============================================================= lançamentos
class ServicoLancamentos:
    def __init__(
        self,
        lancamentos: RepositorioLancamentos,
        contas: RepositorioContas,
        categorias: RepositorioCategorias,
    ) -> None:
        self._lancamentos = lancamentos
        self._contas = contas
        self._categorias = categorias

    def consultar(self, filtro: FiltroLancamentos | None = None) -> list[Lancamento]:
        return self._lancamentos.listar(filtro)

    def obter(self, id: int) -> Lancamento:
        return self._lancamentos.obter(id)

    def registrar(
        self,
        tipo: TipoLancamento | str,
        descricao: str,
        valor: str | Decimal,
        data: date,
        conta_id: int,
        categoria_id: int,
        chave_envio: UUID | None = None,
    ) -> Lancamento:
        lancamento = criar_lancamento(
            tipo,
            descricao=descricao,
            valor=valor,
            data=data,
            conta=self._contas.obter(conta_id),
            categoria=self._categorias.obter(categoria_id),
        )
        return self._lancamentos.adicionar(lancamento, chave_envio)

    def editar(
        self,
        id: int,
        descricao: str,
        valor: str | Decimal,
        data: date,
        conta_id: int,
        categoria_id: int,
    ) -> Lancamento:
        """Edita os dados. O tipo (receita/despesa) é fixo: para trocar, exclua e registre outro."""
        lancamento = self._lancamentos.obter(id)
        lancamento.editar(
            descricao=descricao,
            valor=valor,
            data=data,
            conta=self._contas.obter(conta_id),
            categoria=self._categorias.obter(categoria_id),
        )
        self._lancamentos.atualizar(lancamento)
        return lancamento

    def excluir(self, id: int) -> None:
        self._lancamentos.obter(id)  # confirma que existe (mensagem clara se não existir)
        self._lancamentos.remover(id)


# ============================================================== orçamentos
class ServicoOrcamentos:
    def __init__(
        self,
        orcamentos: RepositorioOrcamentos,
        categorias: RepositorioCategorias,
        lancamentos: RepositorioLancamentos,
    ) -> None:
        self._orcamentos = orcamentos
        self._categorias = categorias
        self._lancamentos = lancamentos

    def definir(self, categoria_id: int, competencia: Competencia, limite: str | Decimal) -> OrcamentoMensal:
        orcamento = OrcamentoMensal(self._categorias.obter(categoria_id), competencia, limite)
        if self._orcamentos.existe(categoria_id, competencia):
            raise RegistroDuplicadoError(
                f"Já existe um orçamento de '{orcamento.categoria.nome}' para {competencia}. Edite o existente."
            )
        return self._orcamentos.adicionar(orcamento)

    def alterar_limite(self, id: int, limite: str | Decimal) -> OrcamentoMensal:
        orcamento = self._orcamentos.obter(id)
        orcamento.limite = limite
        self._orcamentos.atualizar(orcamento)
        return orcamento

    def excluir(self, id: int) -> None:
        self._orcamentos.obter(id)
        self._orcamentos.remover(id)

    def acompanhar(self, competencia: Competencia) -> list[tuple[OrcamentoMensal, SituacaoOrcamento]]:
        lancamentos = self._lancamentos.listar(
            FiltroLancamentos(competencia.primeiro_dia, competencia.ultimo_dia, tipo=TipoLancamento.DESPESA)
        )
        return [(o, o.calcular_situacao(lancamentos)) for o in self._orcamentos.listar(competencia)]


# ============================================================== relatórios
@dataclass(frozen=True)
class PainelFinanceiro:
    """Dados exibidos no painel. Saldo é acumulado; os demais são do mês."""

    competencia: Competencia
    saldo_total: Decimal
    saldos_por_conta: tuple[tuple[ContaFinanceira, Decimal], ...]
    resumo: ResumoMensal
    orcamentos: tuple[tuple[OrcamentoMensal, SituacaoOrcamento], ...]
    ultimos_lancamentos: tuple[Lancamento, ...]

    @property
    def orcamentos_ultrapassados(self) -> tuple[tuple[OrcamentoMensal, SituacaoOrcamento], ...]:
        return tuple((o, s) for o, s in self.orcamentos if s.ultrapassado)


class ServicoRelatorios:
    def __init__(
        self,
        contas: RepositorioContas,
        lancamentos: RepositorioLancamentos,
        orcamentos: RepositorioOrcamentos,
    ) -> None:
        self._contas = contas
        self._lancamentos = lancamentos
        self._orcamentos = orcamentos

    def resumo_mensal(self, competencia: Competencia) -> ResumoMensal:
        lancamentos = self._lancamentos.listar(FiltroLancamentos(competencia.primeiro_dia, competencia.ultimo_dia))
        return ResumoMensal(competencia, lancamentos, self._orcamentos.listar(competencia))

    def painel(self, competencia: Competencia) -> PainelFinanceiro:
        todos = self._lancamentos.listar()  # saldo acumulado precisa de todo o histórico
        orcamentos = self._orcamentos.listar(competencia)
        saldos = tuple((conta, conta.calcular_saldo(todos)) for conta in self._contas.listar())
        do_mes = sorted(
            (l for l in todos if l.ocorreu_em(competencia)),
            key=lambda l: (l.data, l.id or 0),
            reverse=True,
        )
        return PainelFinanceiro(
            competencia=competencia,
            saldo_total=sum((saldo for _, saldo in saldos), ZERO),
            saldos_por_conta=saldos,
            resumo=ResumoMensal(competencia, todos, orcamentos),
            orcamentos=tuple((o, o.calcular_situacao(todos)) for o in orcamentos),
            ultimos_lancamentos=tuple(do_mes[:5]),
        )
