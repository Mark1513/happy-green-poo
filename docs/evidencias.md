# Evidências (resultados observados)

Este arquivo registra apenas o que foi **executado e observado**. Resultados
esperados ficam no roteiro e nos testes; aqui só entram saídas reais.

## 1. Testes automatizados — 10/11/2026

| Execução | Resultado observado | Arquivo com a saída completa |
|---|---|---|
| `pytest -v` (domínio, serviços, interface; sem banco) | **93 passed**, 6 deselected em 6,56 s | [`evidencias/testes_unitarios_e_interface.txt`](evidencias/testes_unitarios_e_interface.txt) |
| `pytest -m integracao -v` (Supabase, schema `happy_green_teste`) | **6 passed** em 59,80 s | [`evidencias/testes_integracao_supabase.txt`](evidencias/testes_integracao_supabase.txt) |

Ambiente: Windows 11, Python 3.12.10, streamlit 1.66.1, psycopg 3.3.6, psycopg-pool 3.3.3, pytest 9.2.0.

O cenário do enunciado roda em dois testes:
- `tests/test_servicos.py::test_cenario_do_enunciado` (repositórios em memória);
- `tests/test_integracao_postgres.py::test_cenario_completo_com_persistencia_e_reinicio`
  (PostgreSQL real: 1.080,00 → aviso de orçamento → 1.050,00 → 1.350,00, e depois
  fecha todas as conexões, cria um pool novo e confere que os dados e os tipos
  `Receita`/`Despesa` continuam lá).

## 2. Banco de dados (Supabase)

| Verificação | Resultado observado |
|---|---|
| Conexão pelo Session pooler `aws-0-us-east-1.pooler.supabase.com:5432` com o usuário `happy_green_app` | Conectou; `current_user = happy_green_app`, PostgreSQL 17.11 |
| Conexão criptografada | `pgconn.ssl_in_use = True` (teste `test_conexao_criptografada`) |
| Consultor de segurança do Supabase após as migrações | Nenhum alerta |
| Carga de demonstração, 1ª execução | "Carga de demonstração concluída." → 3 contas, 9 categorias, 21 lançamentos, 6 orçamentos |
| Carga de demonstração, 2ª execução | "A base já possui dados: carga de demonstração ignorada" (sem duplicar) |

## 3. Execução local no navegador (antes da publicação)

`streamlit run streamlit_app.py` com o banco real:

- Painel em 10/11/2026: saldo total **R$ 12.253,38**, receitas do mês R$ 4.550,00, despesas do mês R$ 2.375,30, resultado R$ 2.174,70. Conferido à mão com os dados de `sql/003` (saldos iniciais 7.650,00 + mês anterior 5.032,50 − 2.603,82 + mês atual 4.550,00 − 2.375,30).
- Aviso de orçamento: "Orçamento de Lazer ultrapassado: gasto de R$ 180,00 para um limite de R$ 150,00 (R$ 30,00 acima)."
- Orçamentos: Alimentação 63,4%, Lazer 120,0% com aviso, Moradia 81,3%, Transporte 79,3%.
- Problemas encontrados e corrigidos nesta verificação: o "R$" virava fórmula no Markdown (corrigido escapando o cifrão) e os 4 indicadores ficavam cortados em telas médias (trocados por uma grade 2 × 2).
- Capturas: [computador](evidencias/local_painel_computador.jpg), [celular 1](evidencias/local_painel_celular_1.jpg), [celular 2](evidencias/local_painel_celular_2.jpg) (viewport 375 × 812).
  Nas capturas do celular, a Carteira aparece com −R$ 39,00; depois disso o saldo inicial dela foi ajustado de 150,00 para 300,00 nos dados fictícios.

## 4. Publicação e verificação pela URL pública — 10/11/2026

**Estado: aplicação publicada e verificada** em <https://happy-green-poo.streamlit.app>.

### Deploy (log do Streamlit Community Cloud, horário UTC)

- 04:39:09 — clone de `Mark1513/happy-green-poo`, branch `main`, arquivo `streamlit_app.py`.
- Ambiente: **Python 3.12.16**; instalados `streamlit==1.66.1`, `psycopg==3.3.6`, `psycopg-binary==3.3.6`, `psycopg-pool==3.3.3` a partir do `requirements.txt`.
- 04:39:33 — `INFO happy_green.config: Criando pool de conexões (host=aws-0-us-east-1.pooler.supabase.com, schema=happy_green)`. A senha não aparece no log.
- Aviso da plataforma (sem efeito): detectou também o `pyproject.toml`, mas usou o `requirements.txt`.

### Cenário do enunciado executado no navegador, pela URL pública

Registros criados com o sufixo "Verificação" para não misturar com a demonstração.

| Passo | Ação | Resultado observado |
|---|---|---|
| 1 | Cadastrar "Conta Verificação" com saldo `0,00` | "Conta 'Conta Verificação' cadastrada." |
| 2 | Categorias "Salário Verificação" (receita), "Alimentação Verificação" e "Transporte Verificação" (despesa) | Três mensagens de cadastro |
| 3–4 | Receita `1.500,00`; despesas `300,00` (alimentação) e `120,00` (transporte) | "Receita 'Salário Verificação' registrada." e as duas despesas registradas |
| 5 | Página Contas | Saldo atual **R$ 1.080,00** ([captura](evidencias/publico_02_saldo_1080.jpg)) |
| 6 | Orçamento de "Alimentação Verificação" `250,00` em 11/2026 | Gasto R$ 300,00, disponível −R$ 50,00, **120,0% do limite** e "Atenção: Limite ultrapassado em R$ 50,00." ([captura](evidencias/publico_03_orcamento_ultrapassado.jpg)) |
| 7 | Editar o transporte para `150,00` | "Lançamento atualizado..." → saldo **R$ 1.050,00** |
| 8 | Excluir a despesa de alimentação (diálogo de confirmação) | "Lançamento excluído..." → saldo **R$ 1.350,00**; orçamento em **0,0% do limite**, sem aviso ([captura do diálogo](evidencias/publico_04_confirmar_exclusao.jpg)) |
| 9 | **Reboot** do app no painel do Community Cloud (log: novo *Starting up* às 04:46:06 UTC) e nova abertura | Saldo continua **R$ 1.350,00** ([captura](evidencias/publico_05_saldo_1350_apos_reboot.jpg)) |
| Extra | Tentar excluir "Conta Verificação" | Recusado: "A conta 'Conta Verificação' possui lançamentos. Exclua ou mova os lançamentos antes." ([captura](evidencias/publico_06_integridade_conta_com_lancamentos.jpg)) |
| Extra | Saldo inicial `12,345` | "Use no máximo 2 casas decimais (centavos)." e nenhuma conta criada |

Outras capturas: [painel publicado](evidencias/publico_01_painel.jpg) e [lançamentos no celular (375 × 812)](evidencias/publico_07_lancamentos_celular.jpg).

### Problemas encontrados nesta verificação

- **Totais do filtro cortados** ("R$ 6....") em larguras médias na página Lançamentos. **Corrigido** no commit `9378265` (totais em uma linha); a versão reimplantada mostrou "11 lançamento(s) no filtro · Receitas: R$ 6.050,00 · Despesas: R$ 2.525,30 · Resultado: R$ 3.524,70", inteira no celular.
- **Erro de operação durante o teste (não é defeito do app):** numa primeira tentativa do teste de validação, o clique não acertou o campo de saldo, e uma conta "Conta Inválida" foi criada com o saldo padrão 0,00. A segunda tentativa, no campo certo, mostrou a mensagem de validação.

### Limpeza

Ao final, os registros de verificação (2 contas, 3 categorias, 2 lançamentos e 1 orçamento) foram removidos do schema `happy_green`. A demonstração voltou a ter 3 contas, 9 categorias, 21 lançamentos e 6 orçamentos.
