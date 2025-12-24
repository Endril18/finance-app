import pandas as pd
from ofxparse import OfxParser
import codecs

# --- Função para ler OFX (Funciona para qualquer banco) ---
def processar_ofx(arquivo):
    try:
        obj_ofx = OfxParser.parse(arquivo)
        transacoes = []
        for t in obj_ofx.account.statement.transactions:
            transacoes.append({
                "Data": t.date.date(),
                "Descrição": t.memo,
                "Valor": float(t.amount),
            })

        df = pd.DataFrame(transacoes)

        # Aplica categoria
        if not df.empty:
            df['Categoria'] = df['Descrição'].apply(categorizar_transacao)

        return df
    except Exception as e:
        return pd.DataFrame()

def categorizar_transacao(descricao):
    """Define a categoria baseada em palavras-chave."""
    if not isinstance(descricao, str):
        return 'Outros'

    desc = descricao.lower()
    if 'uber' in desc or '99' in desc or 'posto' in desc:
        return 'Transporte'
    elif 'ifood' in desc or 'restaurante' in desc or 'mercado' in desc:
        return 'Alimentação'
    elif 'pix' in desc:
        return 'Transferência'
    elif 'aplicação rdb' in desc:
        return 'Investimento'
    elif 'resgate rdb' in desc:
        return 'Resgate Investimento'
    else:
        return 'Outros'