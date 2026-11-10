"""Testes de fumaça da interface com o AppTest do Streamlit.

Os serviços são trocados por versões com repositórios em memória: as páginas
são exercitadas sem banco de dados e sem navegador.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from happy_green.dominio import Competencia, hoje
from happy_green.interface import contexto
from happy_green.servicos import montar_servicos
from tests.fakes import criar_repositorios_em_memoria


@pytest.fixture
def servicos(monkeypatch):
    servicos = montar_servicos(*criar_repositorios_em_memoria())
    monkeypatch.setattr(contexto, "obter_servicos", lambda: servicos)
    return servicos


@pytest.fixture
def com_dados(servicos):
    conta = servicos.contas.criar("Conta Corrente", "0")
    salario = servicos.categorias.criar("Salário", "receita")
    alimentacao = servicos.categorias.criar("Alimentação", "despesa")
    servicos.lancamentos.registrar("receita", "Salário", "1.500,00", hoje(), conta.id, salario.id)
    servicos.lancamentos.registrar("despesa", "Mercado", "300,00", hoje(), conta.id, alimentacao.id)
    servicos.orcamentos.definir(alimentacao.id, Competencia.atual(), "250,00")
    return servicos


def _script_da_pagina(nome_pagina: str) -> None:
    """Script executado pelo AppTest: aviso de demonstração + uma página."""
    import importlib

    from happy_green.interface import componentes

    componentes.aviso_demonstracao()
    importlib.import_module(f"happy_green.interface.paginas.{nome_pagina}").pagina()


def abrir(pagina: str) -> AppTest:
    return AppTest.from_function(_script_da_pagina, args=(pagina,), default_timeout=30).run()


PAGINAS = ["painel", "contas", "categorias", "lancamentos", "orcamentos", "resumo"]


def test_ponto_de_entrada_abre_o_painel(com_dados):
    raiz = Path(__file__).resolve().parent.parent
    app = AppTest.from_file(str(raiz / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "Painel"


@pytest.mark.parametrize("pagina", PAGINAS)
def test_paginas_vazias_carregam_sem_erro(servicos, pagina):
    app = abrir(pagina)
    assert not app.exception
    assert "compartilhados" in app.info[0].value  # aviso de demonstração sempre visível


@pytest.mark.parametrize("pagina", PAGINAS)
def test_paginas_com_dados_carregam_sem_erro(com_dados, pagina):
    app = abrir(pagina)
    assert not app.exception


def test_painel_mostra_indicadores_e_aviso_de_orcamento(com_dados):
    app = abrir("painel")
    valores = {m.label: m.value for m in app.metric}
    assert valores["Saldo total atual"] == "R$ 1.200,00"
    assert valores["Resultado do mês"] == "R$ 1.200,00"
    assert any("Alimentação" in w.value and "ultrapassado" in w.value for w in app.warning)
    assert all("\\$" in w.value for w in app.warning)  # cifrão escapado (não vira fórmula)


def test_cadastrar_conta_pelo_formulario(servicos):
    app = abrir("contas")
    app.text_input[0].input("Carteira")
    app.text_input[1].input("50,25")
    app.button[0].click().run()
    assert not app.exception
    assert any("cadastrada" in s.value for s in app.success)
    assert [c.nome for c in servicos.contas.listar()] == ["Carteira"]


def test_formulario_mostra_erro_de_validacao(servicos):
    app = abrir("contas")
    app.text_input[0].input("Carteira")
    app.text_input[1].input("12,345")
    app.button[0].click().run()
    assert any("2 casas" in e.value for e in app.error)
    assert servicos.contas.listar() == []


def test_registrar_lancamento_pelo_formulario(com_dados):
    app = abrir("lancamentos")
    formulario = [t for t in app.text_input if t.label in ("Descrição", "Valor (R$)")]
    formulario[0].input("Ônibus")
    formulario[1].input("120,00")
    botao = next(b for b in app.button if b.label.startswith("Registrar"))
    botao.click().run()
    assert not app.exception
    assert any("registrada" in s.value for s in app.success)
    assert len(com_dados.lancamentos.consultar()) == 3
