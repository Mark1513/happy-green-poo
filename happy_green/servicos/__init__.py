"""Serviços (casos de uso) e a montagem do conjunto usado pela interface."""

from dataclasses import dataclass

from happy_green.repositorios.base import (
    RepositorioCategorias,
    RepositorioContas,
    RepositorioLancamentos,
    RepositorioOrcamentos,
)
from happy_green.servicos.financeiro import (
    PainelFinanceiro,
    ServicoCategorias,
    ServicoContas,
    ServicoLancamentos,
    ServicoOrcamentos,
    ServicoRelatorios,
)


@dataclass(frozen=True)
class Servicos:
    """Agrupa os serviços para que a interface receba um único objeto."""

    contas: ServicoContas
    categorias: ServicoCategorias
    lancamentos: ServicoLancamentos
    orcamentos: ServicoOrcamentos
    relatorios: ServicoRelatorios


def montar_servicos(
    contas: RepositorioContas,
    categorias: RepositorioCategorias,
    lancamentos: RepositorioLancamentos,
    orcamentos: RepositorioOrcamentos,
) -> Servicos:
    """Injeta os repositórios (reais ou de teste) nos serviços."""
    return Servicos(
        contas=ServicoContas(contas, lancamentos),
        categorias=ServicoCategorias(categorias),
        lancamentos=ServicoLancamentos(lancamentos, contas, categorias),
        orcamentos=ServicoOrcamentos(orcamentos, categorias, lancamentos),
        relatorios=ServicoRelatorios(contas, lancamentos, orcamentos),
    )


__all__ = ["PainelFinanceiro", "Servicos", "montar_servicos"]
