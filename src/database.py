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