# Publicação no Streamlit Community Cloud (gratuito)

O Streamlit Community Cloud executa o `streamlit_app.py` direto do GitHub, em
servidores próprios: o app fica acessível por um link HTTPS público, mesmo
com o seu computador desligado.

Referências oficiais consultadas: [Deploy your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy),
[Secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
e [Manage your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app).

## Pré-requisitos (já prontos neste repositório)

| Arquivo | Função |
|---|---|
| `streamlit_app.py` | Ponto de entrada |
| `requirements.txt` | Dependências instaladas pela hospedagem (versões fixas) |
| `.streamlit/config.toml` | Tema verde Happy Green |
| `.streamlit/secrets.example.toml` | Modelo dos segredos (sem valores reais) |
| `.gitignore` | Impede o envio de `.streamlit/secrets.toml` |

## Passo a passo

1. Acesse <https://share.streamlit.io> e entre com a conta do **GitHub** (`Mark1513`). Autorize o Streamlit a ler os repositórios, se ele pedir.
2. Clique em **Create app** (canto superior direito) e responda **"Yup, I have an app"**.
3. Preencha:
   - **Repository:** `Mark1513/happy-green-poo`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL (opcional):** tente `happy-green-poo`. Se estiver ocupado, o campo avisa; use outra opção, como `happy-green-financas` ou `happy-green-oo`. Não divulgue o link antes de o deploy terminar.
4. Clique em **Advanced settings**:
   - **Python version:** `3.12`
   - **Secrets:** cole **somente a seção `[banco]`** do seu `.streamlit/secrets.toml` (host, port, dbname, user, password, schema, sslmode). **Não** cole a seção `[banco_teste]`.
   - Clique em **Save**.
5. Clique em **Deploy**. A instalação leva alguns minutos; acompanhe pelo log.
6. Teste o link em outro dispositivo (celular com o Wi-Fi desligado, por exemplo).

## Consultar logs

- Com o app aberto e logado como dono, clique em **Manage app** (canto inferior direito) para ver o log em tempo real (instalação, mensagens `INFO` do Happy Green e erros).
- Pelo painel <https://share.streamlit.io>: menu **⋮** do app > **Logs**.
- Os logs só aparecem para quem tem permissão de escrita no repositório. A senha do banco nunca é registrada (o código não a imprime).

## Atualizar a aplicação

- **Código:** faça `git push` na branch `main`; o Community Cloud reimplanta sozinho em poucos segundos ou minutos.
- **Dependências:** altere `requirements.txt` e faça push; a reinstalação é automática.
- **Segredos:** painel > **⋮** > **Settings** > **Secrets** > editar > **Save** (o app reinicia).
- **Reiniciar manualmente:** **Manage app** > **Reboot app**.
- **Estrutura do banco:** novos scripts em `sql/` aplicados no SQL Editor do Supabase (ver `docs/supabase.md`).

## Limitações do plano gratuito (podem afetar a apresentação)

| Limitação | Efeito | Como evitar |
|---|---|---|
| App **hiberna após 12 horas sem acesso** | Ao abrir, aparece "This app has gone to sleep" | Clique em **Yes, get this app back up!** (qualquer visitante pode) e aguarde ~1 min. Abra o link antes da apresentação. |
| Recursos limitados (CPU e memória compartilhadas) | Pode ficar lento com muitos acessos simultâneos | Suficiente para a demonstração |
| Supabase Free **pausa após 7 dias de pouca atividade** | O app mostra "Não foi possível acessar o banco de dados" | Use o app ou o painel do Supabase durante a semana; se pausar, restaure em Supabase > projeto > **Restore** |
| Dados compartilhados e sem login | Qualquer visitante pode alterar a demonstração | Aviso exibido em todas as páginas; recarga possível com `scripts/carregar_demo.py` numa base vazia |

## Estados da publicação

| Estado | Significado |
|---|---|
| Projeto preparado | Código, requisitos, configuração e segredos de exemplo prontos no GitHub |
| Aplicação publicada | O Community Cloud terminou o deploy e gerou o link |
| Aplicação publicada e verificada | Os fluxos principais foram testados pelo link público (ver `docs/evidencias.md`) |
