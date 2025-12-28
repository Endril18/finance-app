import sqlite3
import pandas as pd
import os

# Garante que a pasta data existe
os.makedirs("data", exist_ok=True)
DB_PATH = os.path.join("data", "financas.db")

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabela Transacoes
    c.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE,
            descricao TEXT,
            valor REAL,
            categoria TEXT,
            origem_arquivo TEXT
        )
    ''')
    # Índice para busca rápida
    c.execute('CREATE INDEX IF NOT EXISTS idx_data ON transacoes(data)')

    # Índice para verificar arquivos duplicados rapidamente
    c.execute('CREATE INDEX IF NOT EXISTS idx_arquivo ON transacoes(origem_arquivo)')

    conn.commit()
    conn.close()


def arquivo_ja_existe(nome_arquivo):
    """Verifica se o arquivo já foi importado antes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM transacoes WHERE origem_arquivo = ? LIMIT 1", (nome_arquivo,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

def salvar_novas_transacoes(df, nome_arquivo):
    if df.empty: return 0
    conn = sqlite3.connect(DB_PATH)

    df['origem_arquivo'] = nome_arquivo

    # Renomeia colunas
    df = df.rename(columns={
        'Data': 'data', 'Descrição': 'descricao',
        'Valor': 'valor', 'Categoria': 'categoria'
    })

    # Filtra colunas
    cols = ['data', 'descricao', 'valor', 'categoria', 'origem_arquivo']
    df = df[cols]

    df.to_sql('transacoes', conn, if_exists='append', index=False)
    conn.close()
    return len(df)

def carregar_tudo():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM transacoes ORDER BY data DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def limpar_banco():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM transacoes")
    conn.commit()
    conn.close()

def apagar_periodo_especifico(periodo_yyyy_mm):
    """
    Apaga transações de um mês/ano específico.
    Entrada esperada: string no formato '2025-10'
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # O SQLite armazena data como YYYY-MM-DD.
    # Usamos strftime para pegar só o YYYY-MM e comparar.
    c.execute("DELETE FROM transacoes WHERE strftime('%Y-%m', data) = ?", (periodo_yyyy_mm,))

    linhas_afetadas = c.rowcount
    conn.commit()
    conn.close()
    return linhas_afetadas

# src/database.py

def salvar_edicoes_do_grid(df_original, changes):
    """
    Processa as alterações retornadas pelo st.data_editor.
    changes = {
        'edited_rows': {indice: {coluna: valor}},
        'added_rows': [{coluna: valor}],
        'deleted_rows': [indice]
    }
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # DELETAR (Pelo ID original do banco)
    for index in changes['deleted_rows']:
        # O index do dataframe corresponde à linha que foi carregada
        id_transacao = df_original.iloc[index]['id']
        cursor.execute("DELETE FROM transacoes WHERE id = ?", (int(id_transacao),))

    # ADICIONAR (Novas linhas)
    for nova_linha in changes['added_rows']:
        # Verifica se os campos obrigatórios existem, senão preenche padrão
        data = nova_linha.get('data', pd.Timestamp.today().strftime('%Y-%m-%d'))
        desc = nova_linha.get('descricao', 'Nova Transação')
        valor = float(nova_linha.get('valor', 0.0))
        cat = nova_linha.get('categoria', 'Outros')

        cursor.execute('''
            INSERT INTO transacoes (data, descricao, valor, categoria, origem_arquivo)
            VALUES (?, ?, ?, ?, ?)
        ''', (data, desc, valor, cat, 'Manual'))

    # EDITAR (Atualizar células específicas)
    for index, mudancas in changes['edited_rows'].items():
        id_transacao = df_original.iloc[index]['id']

        for coluna, novo_valor in mudancas.items():
            # Mapeia nome da coluna do DF para nome da coluna no Banco
            # (No seu caso já estão iguais: data, descricao, valor, categoria)
            query = f"UPDATE transacoes SET {coluna} = ? WHERE id = ?"
            cursor.execute(query, (novo_valor, int(id_transacao)))

    conn.commit()
    conn.close()
    return True