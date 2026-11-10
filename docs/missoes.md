# Proposta de 16 missões (etapas de desenvolvimento e aprendizagem)

> **Proposta.** O enunciado menciona 16 missões, mas os textos individuais não
> foram fornecidos. Esta sequência foi criada para organizar o trabalho e o
> estudo; ajuste-a quando os textos oficiais estiverem disponíveis.

| # | Missão | Conceitos / entregas | Onde está no projeto |
|---|---|---|---|
| 1 | Entender o problema e o escopo | Requisitos, fora do escopo (login, bancos, investimentos) | `README.md` |
| 2 | Preparar o ambiente | Python 3.12, ambiente virtual, `requirements.txt`, Git | `requirements*.txt`, `.gitignore` |
| 3 | Política monetária | `Decimal`, 2 casas, `ROUND_HALF_UP`, recusa de `float` | `dominio/dinheiro.py`, `tests/test_dinheiro.py` |
| 4 | Primeira classe com encapsulamento | `__init__`, propriedades, validação, `ContaFinanceira` | `dominio/contas.py` |
| 5 | Herança de identidade | Superclasse `Entidade`, id atribuído uma vez | `dominio/entidade.py` |
| 6 | Categorias e tipos | `Enum`, regra `aceita(tipo)` | `dominio/categorias.py` |
| 7 | Abstração e polimorfismo | `Lancamento(ABC)`, `Receita`, `Despesa`, `calcular_impacto_no_saldo()` | `dominio/lancamentos.py` |
| 8 | Exceções de domínio | Hierarquia `ErroHappyGreen` | `excecoes.py` |
| 9 | Orçamento e composição | `OrcamentoMensal`, `Competencia`, `SituacaoOrcamento` | `dominio/orcamentos.py`, `dominio/tempo.py` |
| 10 | Resumo mensal | `ResumoMensal` compõe `ItemResumoCategoria`; saldo × resultado | `dominio/relatorios.py` |
| 11 | Testes do domínio | pytest sem Streamlit e sem banco | `tests/test_dominio.py`, `tests/test_orcamento_resumo.py` |
| 12 | Serviços e contratos | Casos de uso, repositórios abstratos, injeção de dependência | `servicos/`, `repositorios/base.py`, `tests/fakes.py` |
| 13 | Banco de dados | Schema, restrições, chaves estrangeiras, usuário com menor privilégio | `sql/`, `docs/supabase.md` |
| 14 | Persistência com Psycopg 3 | SQL parametrizado, pool, transações, reconstrução de objetos | `repositorios/postgres.py`, `config.py` |
| 15 | Interface Streamlit | Navegação, formulários, reexecução, mensagens, tema | `streamlit_app.py`, `interface/` |
| 16 | Publicação e apresentação | GitHub, Streamlit Community Cloud, Secrets, verificação pública, roteiro | `docs/publicacao.md`, `docs/roteiro_apresentacao.md` |
