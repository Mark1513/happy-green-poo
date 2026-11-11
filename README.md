# 🌿 Happy Green — gestão financeira pessoal

> ## 🔗 Acesse: **[https://happy-green-poo.streamlit.app](https://happy-green-poo.streamlit.app)**
>
> Publicada no Streamlit Community Cloud e **verificada pela URL pública** em 10/11/2026 (ver [`docs/evidencias.md`](docs/evidencias.md)). Se aparecer "This app has gone to sleep", clique em **Yes, get this app back up!** e aguarde cerca de 1 minuto.
>
> ⚠️ **Demonstração acadêmica:** os dados são fictícios e **compartilhados entre todos os visitantes** — qualquer pessoa pode alterá-los. Não registre informações reais.

Projeto acadêmico de **Programação Orientada a Objetos** em Python: um sistema
de finanças pessoais com interface gráfica em **Streamlit**, persistência real
em **PostgreSQL (Supabase)** e acesso pelo navegador, sem instalar nada.

## Objetivo

Demonstrar, num sistema útil e completo, os conceitos de POO — classes,
encapsulamento, abstração, herança, sobrescrita, polimorfismo, associação,
composição e exceções — separados em camadas (domínio, serviços, repositórios
e interface) e publicados na internet.

## Recursos

- **Contas:** cadastro, edição, listagem e exclusão (só sem lançamentos); saldo atual calculado.
- **Categorias** de receita e de despesa: cadastro, edição e exclusão (só sem uso).
- **Lançamentos** (receitas e despesas): registro, consulta, edição e exclusão, sempre ligados a uma conta e a uma categoria compatível.
- **Filtros** por período, conta, categoria e tipo, com totais do filtro.
- **Painel:** saldo total atual (acumulado), receitas, despesas e resultado do mês, saldos por conta, gráfico e alertas.
- **Orçamento mensal** por categoria de despesa: barra de consumo e aviso quando o limite é ultrapassado.
- **Resumo mensal** por categoria, com participação percentual e situação do orçamento.

Fora do escopo desta versão: login, integração bancária, investimentos e pagamentos.

### Saldo acumulado × resultado mensal

| Indicador | Fórmula | Período |
|---|---|---|
| **Saldo acumulado** (saldo atual) | saldo inicial + receitas − despesas | Todo o histórico da conta |
| **Resultado mensal** | receitas do mês − despesas do mês | Só o mês escolhido (sem saldo inicial) |

## Tecnologias

| Item | Versão |
|---|---|
| Python | 3.12 |
| Streamlit | 1.66.1 |
| Psycopg 3 (`psycopg[binary]`) + `psycopg-pool` | 3.3.6 / 3.3.3 |
| PostgreSQL (Supabase, plano Free) | 17 |
| pytest | 9.2.0 |
| Hospedagem | Streamlit Community Cloud (gratuito) |

## Arquitetura

```text
streamlit_app.py            ← inicialização e navegação
happy_green/
├── dominio/                ← entidades e regras financeiras (POO pura)
│   ├── entidade.py           Entidade (identidade)
│   ├── contas.py             ContaFinanceira
│   ├── categorias.py         Categoria, TipoLancamento
│   ├── lancamentos.py        Lancamento (ABC), Receita, Despesa
│   ├── orcamentos.py         OrcamentoMensal, SituacaoOrcamento
│   ├── relatorios.py         ResumoMensal, ItemResumoCategoria, Totais
│   ├── tempo.py              Competencia, datas
│   └── dinheiro.py           política monetária (Decimal)
├── servicos/               ← casos de uso (sem SQL e sem Streamlit)
├── repositorios/           ← contratos abstratos + PostgreSQL (SQL parametrizado)
├── interface/              ← páginas, formulários e componentes Streamlit
├── config.py               ← st.secrets e pool de conexões
└── excecoes.py             ← exceções de domínio e de infraestrutura
sql/                        ← scripts versionados (estrutura, usuário, dados demo)
scripts/carregar_demo.py    ← carga explícita dos dados fictícios
tests/                      ← pytest (domínio, serviços, interface, integração)
docs/                       ← diagrama, critérios, roteiro, publicação, evidências
```

Fluxo de uma gravação: **página** (formulário) → **serviço** (busca objetos e
aplica a regra) → **domínio** (valida) → **repositório** (SQL) → **PostgreSQL**.

## Decisões de modelagem

- **`Lancamento` é abstrata**: só existem `Receita` e `Despesa`. O valor é sempre positivo; o método sobrescrito `calcular_impacto_no_saldo()` devolve `+valor` ou `-valor`. Saldo, orçamento e resumos apenas somam esses impactos — **nenhum `if` pergunta o subtipo** durante os cálculos.
- **Saldo não é armazenado**: é sempre derivado do saldo inicial e dos lançamentos, então editar ou excluir um lançamento atualiza saldos, resumos e orçamentos automaticamente.
- **`Entidade`** foi acrescentada como superclasse para concentrar a regra do identificador (atribuído pelo banco uma única vez).
- **`Competencia`, `SituacaoOrcamento` e `Totais`** são objetos de valor imutáveis, que deixam as regras de mês e de orçamento explícitas e testáveis.
- **Repositórios abstratos** permitem testar os serviços com repositórios em memória e usar o PostgreSQL na aplicação.
- **O tipo de um lançamento não muda na edição** (para trocar, exclui-se e registra-se outro). O tipo de uma categoria só muda se ela não estiver em uso.

Diagrama completo: [`docs/diagrama_classes.md`](docs/diagrama_classes.md).

## Política monetária

Moeda **BRL**; `Decimal` em Python e `NUMERIC(14, 2)` no PostgreSQL (até
999.999.999.999,99); **2 casas decimais**; entradas com mais de 2 casas são
recusadas; arredondamento **`ROUND_HALF_UP`** apenas em valores calculados
(percentuais). O `Decimal` nunca é criado a partir de `float`: os valores são
digitados como texto (`1.500,00`, `1500,5`, `89.90`) e convertidos com
precisão. Detalhes em [`happy_green/dominio/dinheiro.py`](happy_green/dominio/dinheiro.py).

## Instalação e execução local

Pré-requisitos: Python 3.12 e Git.

```bash
git clone https://github.com/Mark1513/happy-green-poo.git
cd happy-green-poo
python -m venv .venv
```

Ative o ambiente — Windows: `.venv\Scripts\activate` · Linux/macOS: `source .venv/bin/activate`

```bash
pip install -r requirements-dev.txt
```

Configure o banco (ver [Supabase](#supabase)) criando `.streamlit/secrets.toml` a partir de
`.streamlit/secrets.example.toml`, e rode:

```bash
streamlit run streamlit_app.py
```

> Dica (Windows + OneDrive): se a pasta do projeto estiver no OneDrive, crie o
> ambiente virtual fora dela para não sincronizar milhares de arquivos.

## Supabase

Resumo (passo a passo completo em [`docs/supabase.md`](docs/supabase.md)):

1. SQL Editor: rode `sql/001_estrutura.sql` (schema `happy_green`, fora da Data API).
2. SQL Editor: rode `sql/002_usuario_aplicacao.sql` trocando a senha (usuário `happy_green_app`, menor privilégio).
3. **Connect > Session pooler**: copie o host (IPv4) para o `secrets.toml`; usuário `happy_green_app.<ref-do-projeto>`, `sslmode = "require"`.
4. Opcional: `python scripts/carregar_demo.py` (dados fictícios; não duplica se a base já tiver dados).

A aplicação **nunca** cria tabelas, apaga registros ou recarrega dados sozinha.

## Testes

```bash
pytest -v                    # 93 testes: domínio, serviços e interface (sem banco)
pytest -m integracao -v      # 6 testes no Supabase, schema separado happy_green_teste
```

Os testes de integração exigem a seção `[banco_teste]` no `secrets.toml` e são
ignorados quando ela não existe. Saídas reais em [`docs/evidencias.md`](docs/evidencias.md).

## Publicação

Streamlit Community Cloud: repositório `Mark1513/happy-green-poo`, branch `main`,
arquivo `streamlit_app.py`, Python 3.12 e Secrets com a seção `[banco]`.
Passo a passo, logs, atualização e limitações (hibernação após 12 h sem acesso;
pausa do Supabase Free após 7 dias de pouca atividade) em
[`docs/publicacao.md`](docs/publicacao.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/diagrama_classes.md`](docs/diagrama_classes.md) | Diagrama de classes em Mermaid com cardinalidades |
| [`docs/criterios_avaliacao.md`](docs/criterios_avaliacao.md) | Mapa dos critérios e onde são demonstrados |
| [`docs/roteiro_apresentacao.md`](docs/roteiro_apresentacao.md) | Roteiro da apresentação prática |
| [`docs/missoes.md`](docs/missoes.md) | Proposta de 16 missões de desenvolvimento |
| [`docs/supabase.md`](docs/supabase.md) | Configuração do banco |
| [`docs/publicacao.md`](docs/publicacao.md) | Publicação, logs e atualização |
| [`docs/evidencias.md`](docs/evidencias.md) | Resultados observados de testes e fluxos |

## Integrantes e contribuições

Divisão de responsabilidades definida pelo grupo. Cada integrante responde pela sua parte
na apresentação, mas **todos conhecem o projeto inteiro**, como exige o barema.

| # | Integrante | Parte do trabalho | Onde está no repositório |
|---|---|---|---|
| 1 | **Marcos Paulo Santos Mota** | Coordenação, **README** e documentação geral, publicação (GitHub e Streamlit Community Cloud) | `README.md`, `docs/publicacao.md`, `docs/criterios_avaliacao.md`, `docs/missoes.md` |
| 2 | **Eduardo Hernandez Ferreira Mota** | Modelagem orientada a objetos: entidades, abstração, herança e polimorfismo (`Lancamento`, `Receita`, `Despesa`); diagrama de classes | `happy_green/dominio/` (contas, categorias, lançamentos, entidade), `docs/diagrama_classes.md` |
| 3 | **Luciano Schuck Vaiksnoras** | Regras financeiras: política monetária (`Decimal`), orçamento mensal e resumo mensal; serviços (casos de uso) | `happy_green/dominio/dinheiro.py`, `orcamentos.py`, `relatorios.py`, `tempo.py`, `happy_green/servicos/` |
| 4 | **Arthur Conceição Souza** | Banco de dados e persistência: Supabase, scripts SQL, repositórios com Psycopg 3, configuração de segredos | `sql/`, `happy_green/repositorios/`, `happy_green/config.py`, `docs/supabase.md` |
| 5 | **Marcelo Gomes de Souza Junior** | Interface gráfica em Streamlit: páginas, formulários, navegação e identidade visual | `streamlit_app.py`, `happy_green/interface/`, `.streamlit/config.toml`, `assets/` |
| 6 | **Matheus Tavares de Assis Lemos** | Testes automatizados (pytest), evidências e roteiro da apresentação | `tests/`, `docs/evidencias.md`, `docs/roteiro_apresentacao.md` |

> Os commits do repositório foram enviados pela conta GitHub `Mark1513`; a tabela acima registra a
> parte de cada integrante.
