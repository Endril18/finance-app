import streamlit as st
import plotly.express as px
import pandas as pd

# Mapa para traduzir meses
MAPA_MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def renderizar_metricas(df):
    if df.empty:
        st.warning("Sem dados para exibir. Faça o upload de um extrato.")
        return

    # 1. Garantir tipo Data e criar colunas auxiliares
    df['data'] = pd.to_datetime(df['data'])
    df['ano'] = df['data'].dt.year
    df['mes_num'] = df['data'].dt.month

    # --- FILTROS LATERAIS (Cascata) ---
    st.sidebar.header("📅 Filtros de Período")

    anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

    df_ano = df[df['ano'] == ano_selecionado]

    meses_disponiveis = sorted(df_ano['mes_num'].unique())
    opcoes_meses = [0] + meses_disponiveis

    def formatar_mes(opcao):
        if opcao == 0:
            return "Ano Todo"
        return MAPA_MESES.get(opcao, opcao)

    mes_selecionado = st.sidebar.selectbox(
        "Selecione o Mês",
        opcoes_meses,
        format_func=formatar_mes
    )

    # --- APLICAÇÃO DO FILTRO FINAL ---
    if mes_selecionado == 0:
        df_final = df_ano
        periodo_titulo = f"Ano de {ano_selecionado}"
    else:
        df_final = df_ano[df_ano['mes_num'] == mes_selecionado]
        nome_mes = MAPA_MESES.get(mes_selecionado)
        periodo_titulo = f"{nome_mes} de {ano_selecionado}"

    # --- VISUALIZAÇÃO ---
    st.markdown(f"### Visão: {periodo_titulo}")

    # --- CÁLCULOS (Lógica Única e Correta) ---

    # 1. Investimentos (Aplicações)
    # Pega apenas o que você categorizou como 'Investimento' (Aplicação RDB)
    # Como são saídas, o valor é negativo, usamos abs() para somar positivo.
    aplicacoes = df_final[df_final['categoria'] == 'Investimento']['valor'].abs().sum()
    resgates = df_final[df_final['categoria'] == 'Resgate Investimento']['valor'].sum()
    investimento_liquido = aplicacoes - resgates

    # 4. Receitas Reais (Dinheiro Novo)
    # Filtramos tudo que entrou positivo, MAS EXCLUI 'Resgate Investimento'.
    # Motivo: Resgate é transferência interna, não é salário/ganho novo.
    filtro_receitas = (df_final['valor'] > 0) & (df_final['categoria'] != 'Resgate Investimento')
    receitas = df_final[filtro_receitas]['valor'].sum()

    # 5. Despesas (Consumo)
    # Tudo que saiu negativo, exceto o que foi para 'Investimento'
    filtro_despesas = (df_final['valor'] < 0) & (df_final['categoria'] != 'Investimento')
    despesas = df_final[filtro_despesas]['valor'].sum()

    # 6. Saldo Conta (Matemático)
    saldo_conta = df_final['valor'].sum()

    # --- EXIBIÇÃO DOS CARTÕES (4 Colunas) ---
    # Aqui estava a duplicação. Mantivemos apenas este bloco de 4.
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Receitas", f"R$ {receitas:,.2f}")
    col2.metric("Despesas", f"R$ {despesas:,.2f}", delta_color="inverse")
    col3.metric("Investido", f"R$ {investimento_liquido:,.2f}", delta_color="normal")
    col4.metric("Saldo Conta", f"R$ {saldo_conta:,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    c1, c2 = st.columns([1, 1])

    # Gráfico A: Pizza (Corrigido para usar APENAS despesas de consumo)
    # Antes ele estava pegando investimentos também. Agora usa o 'filtro_despesas' criado acima.
    df_pizza = df_final[filtro_despesas].copy()

    if not df_pizza.empty:
        df_pizza['valor_abs'] = df_pizza['valor'].abs()
        fig_pizza = px.pie(
            df_pizza,
            values='valor_abs',
            names='categoria',
            title='Despesas por Categoria',
            hole=0.4
        )
        c1.plotly_chart(fig_pizza, use_container_width=True)
    else:
        c1.info("Nenhuma despesa de consumo neste período.")

    # Gráfico B: Fluxo de Caixa (Mantém tudo para ver a evolução do saldo)
    df_evolucao = df_final.groupby('data')['valor'].sum().reset_index()

    fig_evolucao = px.bar(
        df_evolucao,
        x='data',
        y='valor',
        title='Fluxo de Caixa Diário',
        color='valor',
        color_continuous_scale=['red', 'green']
    )
    c2.plotly_chart(fig_evolucao, use_container_width=True)

    # --- EXTRATO ---
    with st.expander("Ver Extrato Completo"):
        st.dataframe(
            df_final[['data', 'descricao', 'categoria', 'valor']].sort_values('data', ascending=False),
            use_container_width=True,
            hide_index=True
        )