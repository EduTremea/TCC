"""V2: a reescrita devolve as mesmas linhas? Executa as duas e compara.

Resultados diferentes provam que a reescrita esta errada. Resultados iguais
sobre esta base nao provam equivalencia em geral; essa limitacao e assumida.
"""
import pandas as pd


def _normaliza(df):
    """Ordena colunas e linhas para que a ordem nao influencie a comparacao."""
    df = df.reindex(sorted(df.columns), axis=1)
    return df.sort_values(by=list(df.columns)).reset_index(drop=True)


def mesma_semantica(engine, sql_original, sql_reescrita):
    with engine.connect() as conn:
        original = pd.read_sql(sql_original, conn)
        reescrita = pd.read_sql(sql_reescrita, conn)
    if original.shape != reescrita.shape:
        return False
    return _normaliza(original).equals(_normaliza(reescrita))
