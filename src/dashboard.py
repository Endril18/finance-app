import streamlit as st
import plotly.express as px
import pandas as pd

# Mapa para traduzir meses (opcional, mas fica mais bonito em BR)
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

    # A. Filtro de Ano (Pega os anos únicos disponíveis no banco)
    anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

    # Filtragem preliminar pelo ano (para descobrir quais meses exibir)
    df_ano = df[df['ano'] == ano_selecionado]

    # B. Filtro de Mês (Só mostra os meses que existem naquele ano)
    meses_disponiveis = sorted(df_ano['mes_num'].unique())

    # Cria lista de opções: 0 será "O Ano Todo", os outros são os meses
    opcoes_meses = [0] + meses_disponiveis

    def formatar_mes(opcao):
        if opcao == 0:
            return "Ano Todo"
        return MAPA_MESES.get(opcao, opcao)

    mes_selecionado = st.sidebar.selectbox(
        "Selecione o Mês",
        opcoes_meses,
        format_func=formatar_mes # Usa nossa função para mostrar nomes bonitos
    )

    # --- APLICAÇÃO DO FILTRO FINAL ---
    if mes_selecionado == 0:
        # Se escolheu "O Ano Todo", mantém o df filtrado apenas pelo ano
        df_final = df_ano
        periodo_titulo = f"Ano de {ano_selecionado}"
    else:
        # Se escolheu um mês, filtra aquele mês específico
        df_final = df_ano[df_ano['mes_num'] == mes_selecionado]
        nome_mes = MAPA_MESES.get(mes_selecionado)
        periodo_titulo = f"{nome_mes} de {ano_selecionado}"

    # --- VISUALIZAÇÃO ---
    st.markdown(f"### Visão: {periodo_titulo}")

    # Cartões (KPIs)
    col1, col2, col3 = st.columns(3)

    receitas = df_final[df_final['valor'] > 0]['valor'].sum()
    despesas = df_final[df_final['valor'] < 0]['valor'].sum()
    saldo = receitas + despesas

    col1.metric("Receitas", f"R$ {receitas:,.2f}")
    col2.metric("Despesas", f"R$ {despesas:,.2f}", delta_color="inverse")
    col3.metric("Saldo do Período", f"R$ {saldo:,.2f}",
                delta_color="normal" if saldo >= 0 else "inverse")

    # --- LÓGICA DE CÁLCULO ATUALIZADA ---
    # Receitas: Tudo que é positivo menos resgates de investimento
    filtro_receitas = (df_final['valor'] > 0) & (df_final['categoria'] != 'Resgate Investimento')
    receitas = df_final[filtro_receitas]['valor'].sum()

    # Investimentos: Negativos categorizados como 'Investimento' (convertido para positivo)
    filtro_invest = (df_final['categoria'] == 'Investimento') & (df_final['valor'] < 0)
    investimentos = df_final[filtro_invest]['valor'].abs().sum()

    # Despesas Reais: Negativos que NÃO são investimento
    filtro_despesas = (df_final['valor'] < 0) & (df_final['categoria'] != 'Investimento')
    despesas = df_final[filtro_despesas]['valor'].sum() # Continua negativo

    # Saldo em Conta (Matemático): Receitas + (Despesas + Saídas p/ Investimento)
    # Isso reflete o dinheiro real que sobrou na conta corrente
    saldo_conta = df_final['valor'].sum()

    # --- EXIBIÇÃO ---
    col1, col2, col3, col4 = st.columns(4) # Agora são 4 colunas!

    col1.metric("Receitas", f"R$ {receitas:,.2f}")

    # Mostramos despesas em vermelho
    col2.metric("Despesas", f"R$ {despesas:,.2f}", delta_color="inverse")

    # Mostramos investimentos em azul/verde (é positivo para sua vida financeira)
    col3.metric("Investido", f"R$ {investimentos:,.2f}", delta_color="normal")

    # Saldo
    col4.metric("Saldo Conta", f"R$ {saldo_conta:,.2f}")

    st.divider()

    # 2. Gráficos
    c1, c2 = st.columns([1, 1])

    # Gráfico A: Gastos por Categoria (Pizza)
    # Filtramos só despesas e convertemos para positivo para o gráfico entender
    df_despesas = df_final[df_final['valor'] < 0].copy()

    if not df_despesas.empty:
        df_despesas['valor_abs'] = df_despesas['valor'].abs()
        fig_pizza = px.pie(
            df_despesas,
            values='valor_abs',
            names='categoria',
            title='Onde estou gastando?',
            hole=0.4 # Faz virar um gráfico de Rosca (Donut), fica mais moderno
        )
        c1.plotly_chart(fig_pizza, use_container_width=True)
    else:
        c1.info("Nenhuma despesa registrada neste período.")

    # Gráfico B: Evolução Temporal (Linha ou Barra)
    # Agrupa por data para somar gastos do mesmo dia
    df_evolucao = df_final.groupby('data')['valor'].sum().reset_index()

    fig_evolucao = px.bar(
        df_evolucao,
        x='data',
        y='valor',
        title='Fluxo de Caixa (Dia a Dia)',
        color='valor',
        color_continuous_scale=['red', 'green'] # Vermelho negativo, Verde positivo
    )
    c2.plotly_chart(fig_evolucao, use_container_width=True)

    # 3. Extrato Detalhado
    with st.expander("Ver Extrato Completo"):
        # Mostra colunas mais amigáveis
        st.dataframe(
            df_final[['data', 'descricao', 'categoria', 'valor']].sort_values('data', ascending=False),
            use_container_width=True,
            hide_index=True
        )

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

    # --- FILTROS LATERAIS ---
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

    # --- CÁLCULOS (Lógica Unificada) ---

    # Receitas: Tudo que é positivo menos resgates de investimento
    filtro_receitas = (df_final['valor'] > 0) & (df_final['categoria'] != 'Resgate Investimento')
    receitas = df_final[filtro_receitas]['valor'].sum()

    # Investimentos: Saídas categorizadas como 'Investimento'
    filtro_invest = (df_final['categoria'] == 'Investimento') & (df_final['valor'] < 0)
    investimentos = df_final[filtro_invest]['valor'].abs().sum()

    # Despesas Reais: Negativos que NÃO são investimento
    filtro_despesas = (df_final['valor'] < 0) & (df_final['categoria'] != 'Investimento')
    despesas = df_final[filtro_despesas]['valor'].sum()

    # Saldo Matemático da Conta (O que sobrou no banco de verdade)
    saldo_conta = df_final['valor'].sum()

    # --- EXIBIÇÃO DOS CARTÕES (4 Colunas) ---
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Receitas", f"R$ {receitas:,.2f}")
    col2.metric("Despesas", f"R$ {despesas:,.2f}", delta_color="inverse")
    col3.metric("Investido", f"R$ {investimentos:,.2f}", delta_color="normal")
    col4.metric("Saldo Conta", f"R$ {saldo_conta:,.2f}")

    st.divider()

    # --- GRÁFICOS ---
    c1, c2 = st.columns([1, 1])

    # Gráfico A: Pizza (Ajustado para NÃO mostrar investimentos)
    # Só queremos ver para onde foi o dinheiro "gasto", não o guardado.
    df_pizza = df_final[filtro_despesas].copy() # Usa o mesmo filtro das despesas

    if not df_pizza.empty:
        df_pizza['valor_abs'] = df_pizza['valor'].abs()
        fig_pizza = px.pie(
            df_pizza,
            values='valor_abs',
            names='categoria',
            title='Despesas por Categoria (Exceto Investimentos)',
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