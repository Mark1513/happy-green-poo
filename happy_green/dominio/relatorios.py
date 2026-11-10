"""Resumo mensal: receitas, despesas, resultado e totais por categoria."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from happy_green.dominio.categorias import Categoria, TipoLancamento
from happy_green.dominio.dinheiro import ZERO, percentual
from happy_green.dominio.lancamentos import Lancamento
from happy_green.dominio.orcamentos import OrcamentoMensal, SituacaoOrcamento
from happy_green.dominio.tempo import Competencia


@dataclass(frozen=True)
class ItemResumoCategoria:
    """Linha do resumo: total de uma categoria no mês."""

    categoria: Categoria
    total: Decimal
    quantidade: int
    participacao: Decimal  # % do total de receitas ou de despesas do mês
    situacao_orcamento: SituacaoOrcamento | None = None


class ResumoMensal:
    """Consolida os lançamentos de uma competência.

    Composição: o resumo cria e guarda seus próprios ``ItemResumoCategoria``;
    os itens não existem fora do resumo que os criou.

    Diferença importante:
    - resultado mensal = receitas do mês - despesas do mês (só aquele mês);
    - saldo acumulado = saldo inicial + TODOS os lançamentos (ver ContaFinanceira).
    """

    def __init__(
        self,
        competencia: Competencia,
        lancamentos: Iterable[Lancamento],
        orcamentos: Iterable[OrcamentoMensal] = (),
    ) -> None:
        self._competencia = competencia
        self._lancamentos = tuple(l for l in lancamentos if l.ocorreu_em(competencia))
        # Cada impacto é obtido pelo método polimórfico: +valor ou -valor.
        self._impactos = tuple(l.calcular_impacto_no_saldo() for l in self._lancamentos)
        self._itens = self._montar_itens([o for o in orcamentos if o.competencia == competencia])

    @property
    def competencia(self) -> Competencia:
        return self._competencia

    @property
    def total_receitas(self) -> Decimal:
        return sum((impacto for impacto in self._impactos if impacto > 0), ZERO)

    @property
    def total_despesas(self) -> Decimal:
        return -sum((impacto for impacto in self._impactos if impacto < 0), ZERO)

    @property
    def resultado(self) -> Decimal:
        return sum(self._impactos, ZERO)

    @property
    def quantidade_lancamentos(self) -> int:
        return len(self._lancamentos)

    @property
    def itens(self) -> tuple[ItemResumoCategoria, ...]:
        return self._itens

    def itens_do_tipo(self, tipo: TipoLancamento) -> tuple[ItemResumoCategoria, ...]:
        return tuple(item for item in self._itens if item.categoria.tipo is tipo)

    def _montar_itens(self, orcamentos: list[OrcamentoMensal]) -> tuple[ItemResumoCategoria, ...]:
        totais: dict[tuple, list] = {}  # chave da categoria -> [categoria, total, quantidade]
        for lancamento, impacto in zip(self._lancamentos, self._impactos):
            registro = totais.setdefault(lancamento.categoria.chave(), [lancamento.categoria, ZERO, 0])
            registro[1] += abs(impacto)
            registro[2] += 1

        # Categorias com orçamento e sem gasto também aparecem (consumo zero).
        orcamento_por_categoria = {o.categoria.chave(): o for o in orcamentos}
        for chave, orcamento in orcamento_por_categoria.items():
            totais.setdefault(chave, [orcamento.categoria, ZERO, 0])

        base = {TipoLancamento.RECEITA: self.total_receitas, TipoLancamento.DESPESA: self.total_despesas}
        itens = []
        for chave, (categoria, total, quantidade) in totais.items():
            orcamento = orcamento_por_categoria.get(chave)
            itens.append(
                ItemResumoCategoria(
                    categoria=categoria,
                    total=total,
                    quantidade=quantidade,
                    participacao=percentual(total, base[categoria.tipo]),
                    situacao_orcamento=orcamento.calcular_situacao(self._lancamentos) if orcamento else None,
                )
            )
        itens.sort(key=lambda item: (item.categoria.tipo.value, -item.total, item.categoria.nome))
        return tuple(itens)
