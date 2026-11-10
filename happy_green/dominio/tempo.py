"""Datas e competência (mês/ano) usadas nas regras financeiras."""

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from happy_green.excecoes import DadosInvalidosError

# O servidor de hospedagem roda em UTC. Usamos o horário de Brasília (UTC-3,
# sem horário de verão desde 2019) para decidir o que é "hoje" e "mês atual".
FUSO_BRASILIA = timezone(timedelta(hours=-3), "BRT")
DATA_MINIMA = date(2000, 1, 1)

_MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def hoje() -> date:
    """Data atual no horário de Brasília."""
    return datetime.now(FUSO_BRASILIA).date()


def validar_data(valor: date, campo: str = "data") -> date:
    """Garante uma data real entre 01/01/2000 e hoje (lançamentos registram fatos ocorridos)."""
    if isinstance(valor, datetime) or not isinstance(valor, date):
        raise DadosInvalidosError(f"Informe uma {campo} válida.")
    if valor < DATA_MINIMA:
        raise DadosInvalidosError(f"A {campo} deve ser a partir de 01/01/2000.")
    if valor > hoje():
        raise DadosInvalidosError(f"A {campo} não pode estar no futuro.")
    return valor


@dataclass(frozen=True, order=True)
class Competencia:
    """Objeto de valor que representa um mês de referência (ex.: 11/2026).

    É imutável (``frozen``): dois objetos com o mesmo mês e ano são iguais.
    """

    ano: int
    mes: int

    def __post_init__(self) -> None:
        if not isinstance(self.ano, int) or not 2000 <= self.ano <= 2100:
            raise DadosInvalidosError("Ano da competência inválido (use 2000 a 2100).")
        if not isinstance(self.mes, int) or not 1 <= self.mes <= 12:
            raise DadosInvalidosError("Mês da competência inválido (use 1 a 12).")

    @classmethod
    def de_data(cls, data: date) -> "Competencia":
        return cls(data.year, data.month)

    @classmethod
    def atual(cls) -> "Competencia":
        return cls.de_data(hoje())

    @property
    def primeiro_dia(self) -> date:
        return date(self.ano, self.mes, 1)

    @property
    def ultimo_dia(self) -> date:
        return date(self.ano, self.mes, calendar.monthrange(self.ano, self.mes)[1])

    def contem(self, data: date) -> bool:
        return self.primeiro_dia <= data <= self.ultimo_dia

    def anterior(self) -> "Competencia":
        return Competencia(self.ano - 1, 12) if self.mes == 1 else Competencia(self.ano, self.mes - 1)

    def proxima(self) -> "Competencia":
        return Competencia(self.ano + 1, 1) if self.mes == 12 else Competencia(self.ano, self.mes + 1)

    @property
    def rotulo_extenso(self) -> str:
        return f"{_MESES[self.mes - 1]} de {self.ano}"

    def __str__(self) -> str:
        return f"{self.mes:02d}/{self.ano}"
