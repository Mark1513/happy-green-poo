# Roteiro de apresentação prática (~15 minutos)

> Os nomes de quem apresenta cada parte devem ser preenchidos pelo grupo.

## Antes da apresentação (checklist)

- [ ] 1 a 2 dias antes: abrir o link público (acorda o app, que hiberna após 12 h sem acesso) e o painel do Supabase (evita a pausa de 7 dias sem atividade).
- [ ] No dia: abrir o link 5 minutos antes. Se aparecer "This app has gone to sleep", clicar em **Yes, get this app back up!** e aguardar.
- [ ] Ter o repositório do GitHub aberto em outra aba (código, diagrama e testes).
- [ ] Ter um terminal pronto para rodar `pytest -v`.
- [ ] Combinar que outra pessoa pode estar usando a demonstração ao mesmo tempo (os dados são compartilhados).

## 1. Problema e escopo — 1 min (Integrante: ________)

- Gestão financeira pessoal: contas, categorias, receitas, despesas, orçamento mensal e resumos.
- Fora do escopo: login, integração bancária, investimentos e pagamentos.
- Mostrar o aviso de "dados fictícios e compartilhados" no topo.

## 2. Modelagem orientada a objetos — 4 min (Integrante: ________)

1. Abrir `docs/diagrama_classes.md` no GitHub e mostrar o diagrama.
2. `Lancamento` é **abstrata** (`ABC`). Instanciá-la gera `TypeError` (teste `test_lancamento_e_abstrato`).
3. **Sobrescrita**: `Receita.calcular_impacto_no_saldo()` retorna `+valor`; `Despesa`, `-valor`.
4. **Polimorfismo**: `ContaFinanceira.calcular_saldo()` soma os impactos sem perguntar o tipo de cada lançamento.
5. **Encapsulamento**: `valor` não tem setter; `editar()` valida tudo antes de mudar (atômico).
6. **Associação** (lançamento → conta/categoria) × **composição** (orçamento ◆ competência; resumo ◆ itens).
7. **Exceções de domínio**: `CategoriaIncompativelError`, `ExclusaoNaoPermitidaError`...

## 3. Arquitetura em camadas e persistência — 3 min (Integrante: ________)

- Interface → Serviços → Repositórios → PostgreSQL. O domínio não conhece Streamlit nem SQL.
- Repositórios abstratos: a aplicação usa PostgreSQL, os testes usam memória.
- SQL parametrizado (`%s`), pool de conexões, Session pooler com SSL, schema não exposto, usuário com menor privilégio.
- Reconstrução: o banco guarda `tipo`; a fábrica `criar_lancamento` devolve `Receita` ou `Despesa`.

## 4. Demonstração do cenário pelo link público — 5 min (Integrante: ________)

Use nomes que identifiquem a apresentação (ex.: "Conta Apresentação") para não confundir com os dados de demonstração.

| Passo | Ação na tela | Resultado esperado |
|---|---|---|
| 1 | Contas > Nova conta: "Conta Apresentação", saldo `0,00` | Conta listada com saldo R$ 0,00 |
| 2 | Categorias: criar "Salário Apresentação" (receita), "Alimentação Apresentação" e "Transporte Apresentação" (despesa) | Categorias nas duas colunas |
| 3 | Lançamentos > Receita de `1.500,00` | Mensagem de sucesso |
| 4 | Despesa de alimentação `300,00` e de transporte `120,00` | — |
| 5 | Contas | Saldo atual **R$ 1.080,00** |
| 6 | Orçamentos > definir "Alimentação Apresentação" com `250,00` | Barra em 120% e aviso **"Limite ultrapassado em R$ 50,00"** (também no Painel) |
| 7 | Lançamentos > Editar ou excluir > transporte para `150,00` | Saldo **R$ 1.050,00** |
| 8 | Excluir a despesa de alimentação (confirmar no diálogo) | Saldo **R$ 1.350,00**; orçamento volta a 0% |
| 9 | Atualizar a página (F5) ou abrir o link no celular | Os dados continuam lá (persistência) |
| 10 | Tentar excluir "Conta Apresentação" | Mensagem: a conta possui lançamentos (integridade) |
| 11 | Digitar `12,345` em um valor | Mensagem: no máximo 2 casas decimais |

Depois, explicar a diferença no Painel: **saldo acumulado** (todo o histórico) × **resultado mensal** (só o mês).

## 5. Testes — 1 min (Integrante: ________)

- `pytest -v`: 93 testes de domínio, serviços e interface (sem banco).
- `pytest -m integracao -v`: 6 testes no Supabase (schema de testes), incluindo o reinício da aplicação.
- Mostrar `docs/evidencias/`.

## 6. Encerramento — 1 min

- Limitações: demonstração pública e compartilhada, sem login; hibernação do app gratuito; pausa do Supabase gratuito.
- Próximos passos: login com Supabase Auth e dados por usuário, metas de economia, exportação CSV.
- Ao final, se quiser, excluir os registros "Apresentação" criados.
