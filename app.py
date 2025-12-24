import streamlit as st
import time
from src import tratamento, database, dashboard

# Configuração DEVE ser a primeira linha executável
st.set_page_config(page_title="Relatório de Finanças", layout="wide")

# Inicializa banco
database.inicializar_db()

# Inicializa chave única para o uploader
if 'uploader_key' not in st.session_state:
    st.session_state['uploader_key'] = 0

# --- SIDEBAR: Área de Upload ---
st.sidebar.title("Menu")
st.sidebar.subheader("Importar Arquivos")

arquivo = st.sidebar.file_uploader("Upload de OFX", type=["ofx"], key=f"upload_{st.session_state['uploader_key']}")

if arquivo:

    # VERIFICAÇÃO DE DUPLICIDADE
    if database.arquivo_ja_existe(arquivo.name):
        st.warning(f"O arquivo '{arquivo.name}' já foi importado anteriormente!")
        st.stop() # Para a execução aqui, impedindo o processamento
    # Mostra um spinner enquanto processa

    with st.spinner("Lendo arquivo..."):
        # Tratamento (Lógica)
        df_novo = tratamento.processar_ofx(arquivo)
        df_novo['Categoria'] = df_novo['Descrição'].apply(tratamento.categorizar_transacao)

        st.info("🔎 **Prévia dos Dados Detectados** (Verifique antes de salvar)")

        # Mostra os dados (editável se quiser conferir detalhes)
        st.dataframe(df_novo.head(5), use_container_width=True)

        col_btn1, col_btn2 = st.columns([1, 4])

        if col_btn1.button("Confirmar e Salvar", type="primary"):
            qtd = database.salvar_novas_transacoes(df_novo, arquivo.name)

            # Notificação Flutuante (Toast)
            st.toast(f"Sucesso! {qtd} transações salvas.", icon='🎉')

            # Mudamos a chave do uploader (ele vai nascer novo e vazio)
            st.session_state['uploader_key'] += 1

            # Pequena pausa visual (opcional) para o usuário ver que clicou
            time.sleep(0.5)

            # Recarrega a página.
            # Como o uploader estará vazio, o bloco "if arquivo:" não roda.
            # Resultado: A prévia some e volta a mostrar o Dashboard.
            st.rerun()

# --- DASHBOARD ---
# Se tiver arquivo pendente, focamos na importação. Se não, mostramos os gráficos.
if not arquivo:
    st.title("Painel de Controle")
    df_total = database.carregar_tudo()
    dashboard.renderizar_metricas(df_total)

    # Rodapé / Opções Extras
    st.divider()
    if st.sidebar.checkbox("Mostrar Opções de Admin"):
        if st.sidebar.button("🗑️ Limpar Banco de Dados"):
            database.limpar_banco()
            st.warning("Banco de dados reiniciado!")
            st.rerun()
