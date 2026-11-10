"""Happy Green: sistema de gestão financeira pessoal.

Camadas do pacote:
- dominio: entidades e regras financeiras (POO pura, sem Streamlit e sem banco).
- servicos: coordenação dos casos de uso.
- repositorios: persistência no PostgreSQL e reconstrução dos objetos.
- interface: páginas e formulários Streamlit.
- config: leitura dos segredos e criação do pool de conexões.
"""
