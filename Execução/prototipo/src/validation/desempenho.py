"""V3: custo estimado pelo planejador e tempo medido com as duas consultas intercaladas.

O custo e o criterio de ganho (nao depende da maquina). O tempo e complemento:
mede-se original e reescrita alternadas, cinco pares, e usa-se a mediana das
razoes. O limiar 1,15 fica acima da maior razao obtida ao medir uma consulta
contra ela mesma (1,148).
"""
import re
import statistics

from sqlalchemy import text

LIMIAR_TEMPO = 1.15
PROTOCOLO = ("medicao apos a verificacao de resultado; nenhum modelo carregado; "
             "1 aquecimento de cada + 5 pares intercalados com ordem alternada; "
             "mediana das razoes; mais rapida se >= 1,15")


def normalizar_sql(sql):
    return re.sub(r"\s+", " ", sql or "").strip().rstrip(";").strip().lower()


def mesma_consulta(sql_a, sql_b):
    """True quando a reescrita e a propria consulta original, a menos de espacos, caixa e ';'."""
    return normalizar_sql(sql_a) == normalizar_sql(sql_b)


def custo_estimado(engine, sql):
    """Custo total do plano, sem executar a consulta."""
    with engine.connect() as conn:
        plano = conn.execute(text(f"EXPLAIN (FORMAT JSON) {sql}")).scalar_one()
    return plano[0]["Plan"]["Total Cost"]


def medir(engine, sql):
    """Executa com EXPLAIN ANALYZE e devolve (custo, tempo_ms, linhas) do no raiz."""
    with engine.connect() as conn:
        plano = conn.execute(text(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}")).scalar_one()
    raiz = plano[0]["Plan"]
    return raiz["Total Cost"], raiz["Actual Total Time"], raiz["Actual Rows"]


def medir_intercalado(engine, sql_original, sql_reescrita, pares=5):
    """Um aquecimento de cada consulta, depois `pares` pares com a ordem alternada."""
    medir(engine, sql_original)
    medir(engine, sql_reescrita)
    tempos = {"original": [], "reescrita": []}
    custo = {}
    linhas = {}
    for i in range(pares):
        ordem = [("original", sql_original), ("reescrita", sql_reescrita)]
        if i % 2 == 1:
            ordem.reverse()
        for nome, sql in ordem:
            custo[nome], tempo, linhas[nome] = medir(engine, sql)
            tempos[nome].append(tempo)
    razoes = [a / b if b > 0 else float("inf") for a, b in zip(tempos["original"], tempos["reescrita"])]
    return {
        "tempo_original_ms": statistics.median(tempos["original"]),
        "tempo_reescrita_ms": statistics.median(tempos["reescrita"]),
        "razao_mediana": statistics.median(razoes),
        "custo_original": custo["original"],
        "custo_reescrita": custo["reescrita"],
        "linhas_original": linhas["original"],
        "linhas_reescrita": linhas["reescrita"],
        "razoes": razoes,
    }
