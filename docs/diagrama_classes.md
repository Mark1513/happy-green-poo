# Diagrama de classes — Happy Green

Diagramas em Mermaid (o GitHub os desenha automaticamente). Nomes, atributos e
métodos correspondem ao código em `happy_green/`.

## 1. Domínio (`happy_green/dominio`)

```mermaid
classDiagram
    direction TB

    class Entidade {
        -_id: int | None
        +id: int | None
        +atribuir_id(id: int) None
        +mesma_entidade(outra: Entidade) bool
        +chave() tuple
    }

    class ContaFinanceira {
        -_nome: str
        -_saldo_inicial: Decimal
        +nome: str
        +saldo_inicial: Decimal
        +calcular_saldo(lancamentos) Decimal
    }

    class Categoria {
        -_nome: str
        -_tipo: TipoLancamento
        +nome: str
        +tipo: TipoLancamento
        +aceita(tipo: TipoLancamento) bool
        +alterar_tipo(novo_tipo) None
    }

    class TipoLancamento {
        <<enumeration>>
        RECEITA
        DESPESA
        +rotulo: str
    }

    class Lancamento {
        <<abstract>>
        -_descricao: str
        -_valor: Decimal
        -_data: date
        +tipo: TipoLancamento*
        +calcular_impacto_no_saldo()* Decimal
        +editar(descricao, valor, data, conta, categoria) None
        +pertence_a(conta) bool
        +ocorreu_em(competencia) bool
    }

    class Receita {
        +tipo: TipoLancamento
        +calcular_impacto_no_saldo() Decimal
    }

    class Despesa {
        +tipo: TipoLancamento
        +calcular_impacto_no_saldo() Decimal
    }

    class OrcamentoMensal {
        -_limite: Decimal
        +limite: Decimal
        +calcular_consumo(lancamentos) Decimal
        +calcular_situacao(lancamentos) SituacaoOrcamento
    }

    class Competencia {
        <<objeto de valor>>
        +ano: int
        +mes: int
        +primeiro_dia: date
        +ultimo_dia: date
        +contem(data) bool
        +atual()$ Competencia
    }

    class SituacaoOrcamento {
        <<objeto de valor>>
        +limite: Decimal
        +consumido: Decimal
        +disponivel: Decimal
        +percentual_consumido: Decimal
        +ultrapassado: bool
        +excedente: Decimal
    }

    class ResumoMensal {
        +total_receitas: Decimal
        +total_despesas: Decimal
        +resultado: Decimal
        +itens: tuple
        +itens_do_tipo(tipo) tuple
    }

    class ItemResumoCategoria {
        +total: Decimal
        +quantidade: int
        +participacao: Decimal
    }

    class Totais {
        <<objeto de valor>>
        +receitas: Decimal
        +despesas: Decimal
        +resultado: Decimal
        +calcular(lancamentos)$ Totais
    }

    Entidade <|-- ContaFinanceira
    Entidade <|-- Categoria
    Entidade <|-- Lancamento
    Entidade <|-- OrcamentoMensal
    Lancamento <|-- Receita
    Lancamento <|-- Despesa

    Lancamento "0..*" --> "1" ContaFinanceira : conta
    Lancamento "0..*" --> "1" Categoria : categoria
    Categoria "0..*" --> "1" TipoLancamento : tipo
    OrcamentoMensal "0..*" --> "1" Categoria : categoria (só despesa)
    OrcamentoMensal "1" *-- "1" Competencia : competência
    ResumoMensal "1" *-- "0..*" ItemResumoCategoria : itens
    ResumoMensal "1" *-- "1" Totais : totais
    ResumoMensal "0..*" --> "1" Competencia : mês
    ItemResumoCategoria "0..*" --> "1" Categoria
    ItemResumoCategoria "1" --> "0..1" SituacaoOrcamento
    OrcamentoMensal ..> SituacaoOrcamento : cria
    ContaFinanceira ..> Lancamento : soma impactos
```

Leitura das relações:

| Relação | Tipo | Por quê |
|---|---|---|
| `Lancamento` → `ContaFinanceira` / `Categoria` | Associação (N:1) | A conta e a categoria existem por conta própria; vários lançamentos apontam para elas. |
| `OrcamentoMensal` ◆ `Competencia` | Composição (1:1) | A competência é um objeto de valor sem identidade; não existe fora do orçamento. |
| `ResumoMensal` ◆ `ItemResumoCategoria` | Composição (1:N) | O resumo cria e guarda seus itens; eles somem com o resumo. |
| `Receita`/`Despesa` ▷ `Lancamento` ▷ `Entidade` | Herança | Reaproveitam validação e identidade; sobrescrevem `calcular_impacto_no_saldo()` e `tipo`. |

## 2. Serviços e repositórios

```mermaid
classDiagram
    direction LR

    class ServicoContas
    class ServicoCategorias
    class ServicoLancamentos
    class ServicoOrcamentos
    class ServicoRelatorios
    class Servicos {
        <<agregador>>
    }

    class RepositorioContas {
        <<abstract>>
        +listar()* list
        +obter(id)* ContaFinanceira
        +adicionar(conta)* ContaFinanceira
        +atualizar(conta)*
        +remover(id)*
    }
    class RepositorioCategorias {
        <<abstract>>
        +em_uso(id)* bool
    }
    class RepositorioLancamentos {
        <<abstract>>
        +listar(filtro)* list
        +adicionar(lancamento, chave_envio)* Lancamento
        +existe_para_conta(conta_id)* bool
    }
    class RepositorioOrcamentos {
        <<abstract>>
        +existe(categoria_id, competencia)* bool
    }

    class RepositorioPostgres {
        -_pool: ConnectionPool
        #_conexao() contexto
    }
    class ContasPostgres
    class CategoriasPostgres
    class LancamentosPostgres
    class OrcamentosPostgres

    Servicos "1" *-- "1" ServicoContas
    Servicos "1" *-- "1" ServicoCategorias
    Servicos "1" *-- "1" ServicoLancamentos
    Servicos "1" *-- "1" ServicoOrcamentos
    Servicos "1" *-- "1" ServicoRelatorios

    ServicoContas --> RepositorioContas
    ServicoContas --> RepositorioLancamentos
    ServicoCategorias --> RepositorioCategorias
    ServicoLancamentos --> RepositorioLancamentos
    ServicoLancamentos --> RepositorioContas
    ServicoLancamentos --> RepositorioCategorias
    ServicoOrcamentos --> RepositorioOrcamentos
    ServicoRelatorios --> RepositorioLancamentos

    RepositorioPostgres <|-- ContasPostgres
    RepositorioPostgres <|-- CategoriasPostgres
    RepositorioPostgres <|-- LancamentosPostgres
    RepositorioPostgres <|-- OrcamentosPostgres
    RepositorioContas <|.. ContasPostgres
    RepositorioCategorias <|.. CategoriasPostgres
    RepositorioLancamentos <|.. LancamentosPostgres
    RepositorioOrcamentos <|.. OrcamentosPostgres
```

Os serviços dependem dos **contratos abstratos**; a aplicação injeta as
implementações PostgreSQL (`montar_repositorios_postgres`) e os testes injetam
implementações em memória (`tests/fakes.py`). Cada classe `*Postgres` herda de
duas bases: `RepositorioPostgres` (pool e tradução de erros) e o contrato.
