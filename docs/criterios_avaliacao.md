# Mapa dos critérios de avaliação

Cada requisito do enunciado e onde ele é demonstrado (código, teste ou tela).
Os links apontam para os arquivos do repositório.

## POO (seção 4 do enunciado)

| Critério | Onde está | Como mostrar na apresentação |
|---|---|---|
| Classes, objetos, atributos e métodos | [`dominio/`](../happy_green/dominio) — `ContaFinanceira`, `Categoria`, `Lancamento`, `OrcamentoMensal`, `ResumoMensal` | Abrir `contas.py`: atributos privados + `calcular_saldo()` |
| Construtores `__init__` com inicialização válida | [`contas.py`](../happy_green/dominio/contas.py), [`lancamentos.py`](../happy_green/dominio/lancamentos.py) (`_validar_e_atribuir`) | Teste `test_valor_deve_ser_estritamente_positivo` |
| Encapsulamento (propriedades, invariantes) | `@property` + setters validados; `valor` do lançamento sem setter; `editar()` atômico; id atribuído uma vez ([`entidade.py`](../happy_green/dominio/entidade.py)) | Testes `test_edicao_atomica_nao_altera_nada_se_invalida`, `test_valor_do_lancamento_nao_tem_setter`, `test_id_atribuido_uma_unica_vez` |
| Abstração (`ABC`, `abstractmethod`) | `Lancamento(Entidade, ABC)` com `tipo` e `calcular_impacto_no_saldo()` abstratos; contratos de repositório ([`base.py`](../happy_green/repositorios/base.py)) | `test_lancamento_e_abstrato` (instanciar dá `TypeError`) |
| Herança | `Entidade` → `ContaFinanceira`, `Categoria`, `Lancamento`, `OrcamentoMensal`; `Lancamento` → `Receita`, `Despesa`; `RepositorioPostgres` → `ContasPostgres`... | Diagrama em [`diagrama_classes.md`](diagrama_classes.md) |
| Sobrescrita | `Receita.calcular_impacto_no_saldo()` retorna `+valor`; `Despesa` retorna `-valor` | `test_receita_aumenta_e_despesa_diminui` |
| Polimorfismo sem `if` de subtipo | `ContaFinanceira.calcular_saldo`, `OrcamentoMensal.calcular_consumo`, `Totais.calcular`, `ResumoMensal` só chamam o método polimórfico; a fábrica usa dicionário (`CLASSES_DE_LANCAMENTO`) | `test_saldo_calculado_polimorficamente`; tela Lançamentos (valores com sinal) |
| Associação | `Lancamento` → `ContaFinanceira` e `Categoria`; `OrcamentoMensal` → `Categoria` | Diagrama (cardinalidades N:1) |
| Composição | `OrcamentoMensal` contém `Competencia`; `ResumoMensal` cria seus `ItemResumoCategoria` e `Totais`; `Servicos` agrega os serviços | [`orcamentos.py`](../happy_green/dominio/orcamentos.py), [`relatorios.py`](../happy_green/dominio/relatorios.py) |
| Exceções de domínio e tratamento | Hierarquia em [`excecoes.py`](../happy_green/excecoes.py); tradução de erros do banco em `RepositorioPostgres._conexao`; mensagens na tela por `componentes.executar` | Tentar excluir uma conta com lançamentos na tela Contas |
| Domínio testável sem Streamlit e sem banco | `tests/test_dominio.py`, `tests/test_orcamento_resumo.py`, `tests/test_servicos.py` (repositórios em memória) | `pytest -v` (93 testes) |

## Organização (seção 5)

| Camada | Pasta | Regra respeitada |
|---|---|---|
| Domínio | `happy_green/dominio` | Não importa Streamlit nem psycopg |
| Serviços | `happy_green/servicos` | Coordenam casos de uso; não conhecem SQL nem telas |
| Repositórios | `happy_green/repositorios` | Todo o SQL fica aqui; reconstroem `Receita`/`Despesa` (`_montar_lancamento`) |
| Interface | `happy_green/interface`, `streamlit_app.py` | Sem SQL e sem regra financeira (totais vêm de `Totais`/`ResumoMensal`) |
| Configuração | `happy_green/config.py`, `.streamlit/` | Segredos via `st.secrets`; pool de conexões |
| Testes e documentação | `tests/`, `docs/`, `README.md` | — |

## Regras financeiras e integridade (seção 6)

| Regra | Domínio | Banco |
|---|---|---|
| `Decimal` / `NUMERIC(14,2)`, BRL, 2 casas, `ROUND_HALF_UP`, sem `float` | [`dinheiro.py`](../happy_green/dominio/dinheiro.py) | `numeric(14, 2)` em `sql/001` |
| Valores estritamente positivos; sinal pelo polimorfismo | `Lancamento._validar_e_atribuir` | `CHECK (valor > 0)` |
| Saldo calculado (sem dado redundante) | `ContaFinanceira.calcular_saldo` | Não existe coluna de saldo atual |
| Edição/exclusão atualizam saldos, resumos e orçamentos | Tudo é recalculado a cada leitura | — |
| Campos obrigatórios, datas, compatibilidade categoria × lançamento | `validar_texto`, `validar_data`, `Categoria.aceita` | `CHECK`s e FK composta `(categoria_id, tipo)` |
| Impedir exclusões que deixariam referências inválidas | `ServicoContas.excluir`, `ServicoCategorias.excluir` | `ON DELETE RESTRICT` |
| Orçamento único por categoria e mês | `ServicoOrcamentos.definir` | `UNIQUE (categoria_id, competencia)` |
| Mensagens compreensíveis; detalhes só no log | `componentes.executar/carregar`, `MENSAGENS_RESTRICOES` | — |
| Transações | Cada operação em `with pool.connection()` (commit/rollback); carga demo em bloco único | — |

## Persistência e Streamlit (seção 7)

| Requisito | Onde |
|---|---|
| Session pooler (IPv4) + SSL exigido | `config.py` (`sslmode`), [`supabase.md`](supabase.md); teste `test_conexao_criptografada` |
| Schema não exposto pela Data API | `happy_green` (fora de "Exposed schemas"); `REVOKE` para `anon`/`authenticated` em `sql/002` |
| Scripts SQL versionados | `sql/001`, `sql/002`, `sql/003` |
| `st.secrets` (local, nuvem, exemplo) | `.streamlit/secrets.toml` (ignorado), Secrets do Cloud, `.streamlit/secrets.example.toml` |
| Sem persistência em memória / `session_state` | `session_state` guarda só filtros, mensagem pendente e a chave de envio |
| Formulários com envio explícito; sem duplicação | `st.form` em todas as gravações; `chave_envio` + `ON CONFLICT DO NOTHING` (`test_reenvio_nao_duplica_no_banco`) |
| Não recriar/apagar/recarregar dados a cada execução | Nenhum DDL ou carga roda no app; carga só por `scripts/carregar_demo.py` |
| Atualizar dados após alterações | `st.rerun()` depois de cada gravação; nenhum cache de dados para invalidar |
| Conexões concorrentes | `ConnectionPool` único (`st.cache_resource`), conexões emprestadas por operação |
| Dados sobrevivem a reinício | `test_cenario_completo_com_persistencia_e_reinicio` (fecha o pool e cria outro) |

## Interface (seção 8) e publicação (seção 9)

| Requisito | Onde |
|---|---|
| Identidade verde, contraste e tipografia | `.streamlit/config.toml` (verde #1B6E3C, contraste 6,3:1), `assets/logo.svg` |
| Navegação entre as 6 páginas | `streamlit_app.py` (`st.navigation`) |
| Formulários, tabelas, filtros, mensagens, estados vazios, confirmação | `interface/paginas/*`, `componentes.confirmar_exclusao` |
| Computador e celular | Capturas em `docs/evidencias/` |
| Gráficos com dados reais | Painel e Resumo (`componentes.grafico_por_categoria`) |
| Arquivos de publicação | `streamlit_app.py`, `requirements.txt`, `.streamlit/config.toml`, `secrets.example.toml`, `.gitignore` |
| Passo a passo de publicação, logs e atualização | [`publicacao.md`](publicacao.md) |

## Testes e documentação (seção 10)

| Requisito | Onde |
|---|---|
| Cálculos, polimorfismo, validações, orçamento, edição e exclusão | `tests/test_dominio.py`, `tests/test_orcamento_resumo.py`, `tests/test_servicos.py` |
| Cenário do enunciado | `test_cenario_do_enunciado` (memória) e `test_cenario_completo_com_persistencia_e_reinicio` (Supabase) |
| Integração separada da demonstração | schema `happy_green_teste`, `pytest -m integracao` |
| Diagrama Mermaid | [`diagrama_classes.md`](diagrama_classes.md) |
| Roteiro de apresentação | [`roteiro_apresentacao.md`](roteiro_apresentacao.md) |
| Evidências reais | [`evidencias.md`](evidencias.md) |
