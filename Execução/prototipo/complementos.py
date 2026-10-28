"""Duas tabelas complementares do conjunto final: tipos de erro das reescritas invalidas e latencia de inferencia.

Uso:
    uv run python complementos.py      (depois de analise_v4.py; precisa do banco tcc para recontar as linhas)

Tipos de erro: executa de novo cada reescrita invalida por resultado da base controlada,
conta as linhas e classifica a diferenca em mais linhas, menos linhas ou mesmo numero
de linhas com valores diferentes.

Latencia: tempo que o modelo levou para responder (coluna tempo_llm_ms), por modelo e
fase, nas duas bases. Os locais rodam em CPU; o tempo do modelo pago inclui a rede.
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db import get_engine

PASTA = next(p for p in [Path("results/final_v4"), Path("../resultados")] if (p / "tcc_execucoes_classificadas.csv").exists())
ORDEM = ["llama3.2 (3B)", "llama3 (8B)", "gpt-4o"]


def contar(conn, sql):
    return conn.execute(text(f"SELECT count(*) FROM ({sql.strip().rstrip(';')}) AS t")).scalar_one()


def tipos_de_erro():
    d = pd.read_csv(PASTA / "tcc_execucoes_classificadas.csv")
    inval = d[d["categoria5"] == "invalida_resultado"].drop(columns=["linhas_original", "linhas_reescrita"])
    inval["categoria_consulta"] = inval["query_id"].str.rsplit("_", n=1).str[0]
    distintas = inval[["query_id", "sql_original", "sql_reescrita"]].drop_duplicates()

    linhas = []
    with get_engine().connect() as conn:
        originais = {q: contar(conn, s) for q, s in distintas[["query_id", "sql_original"]].drop_duplicates().itertuples(index=False)}
        for query_id, _, reescrita in distintas.itertuples(index=False):
            n, o = contar(conn, reescrita), originais[query_id]
            tipo = "mais linhas" if n > o else ("menos linhas" if n < o else "mesmo numero, valores diferentes")
            linhas.append({"query_id": query_id, "sql_reescrita": reescrita, "linhas_original": o, "linhas_reescrita": n, "tipo": tipo})
    inval = inval.merge(pd.DataFrame(linhas), on=["query_id", "sql_reescrita"], how="left")

    def tabela(coluna):
        t = inval.groupby([coluna, "modelo"]).size().unstack("modelo").reindex(columns=ORDEM).fillna(0).astype(int)
        t["total"] = t.sum(axis=1)
        return t.reset_index()

    tabela("tipo").to_csv(PASTA / "tcc_invalidas_por_tipo.csv", index=False)
    tabela("categoria_consulta").to_csv(PASTA / "tcc_invalidas_por_categoria.csv", index=False)
    inval[["modelo", "config", "rodada", "query_id", "tipo", "linhas_original", "linhas_reescrita", "sql_reescrita"]] \
        .to_csv(PASTA / "tcc_invalidas_detalhe.csv", index=False)
    print(f"invalidas por resultado: {len(inval)} execucoes, {len(distintas)} reescritas distintas")
    print(tabela("tipo").to_string(index=False))


def latencia():
    partes = []
    for base in ["tcc", "tpch"]:
        d = pd.read_csv(PASTA / f"{base}_execucoes_classificadas.csv", usecols=["modelo", "config", "tempo_llm_ms"])
        d["base"] = base
        partes.append(d)
    d = pd.concat(partes)
    d["segundos"] = d["tempo_llm_ms"] / 1000
    por_fase = d.groupby(["base", "modelo", "config"])["segundos"].median().unstack("config").round(1)
    por_fase["mediana"] = d.groupby(["base", "modelo"])["segundos"].median().round(1)
    por_fase["p90"] = d.groupby(["base", "modelo"])["segundos"].quantile(0.9).round(1)
    por_fase = por_fase.reset_index()
    por_fase["modelo"] = pd.Categorical(por_fase["modelo"], ORDEM)
    por_fase = por_fase.sort_values(["base", "modelo"])
    por_fase.to_csv(PASTA / "latencia_inferencia.csv", index=False)
    print(por_fase.to_string(index=False))


if __name__ == "__main__":
    tipos_de_erro()
    print()
    latencia()
