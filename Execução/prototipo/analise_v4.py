"""Classifica cada execucao em cinco categorias e gera as tabelas e figuras do conjunto final.

Uso:
    uv run python analise_v4.py          (saida em results/final_v4/)

Categorias, aplicadas nesta ordem:
    invalida_sintaxe    nao executa (inclui estouro de tempo ou de disco)
    invalida_resultado  executa, mas devolve linhas diferentes
    sem_mudanca         devolveu a propria consulta original
    valida_sem_ganho    mesmo resultado, custo estimado igual ou maior
    otimizada           mesmo resultado, custo estimado menor

Le as rodadas "v3-*" dos bancos tcc e tpch: a fase C0 vem das rodadas cujo nome
contem "limpo" e as fases C1 a C3 das que contem "stats". As rodadas
"fmt-completo" sao a variante de esquema completo em C1.
"""
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.db import get_engine

SAIDA = Path("results/final_v4")
MODELOS = {"llama3.2": "llama3.2 (3B)", "llama3": "llama3 (8B)", "gpt-4o": "gpt-4o"}
ORDEM = list(MODELOS.values())
NIVEIS = ["C0", "C1", "C2", "C3"]
CATS = ["invalida_sintaxe", "invalida_resultado", "sem_mudanca", "valida_sem_ganho", "otimizada"]
ROTULOS = {"invalida_sintaxe": "não executa", "invalida_resultado": "inválida por resultado",
           "sem_mudanca": "sem mudança", "valida_sem_ganho": "válida sem ganho", "otimizada": "otimizada"}
CORES = {"invalida_sintaxe": "#8c8c8c", "invalida_resultado": "#b22222", "sem_mudanca": "#d9c27a",
         "valida_sem_ganho": "#7fa7c9", "otimizada": "#2d6a4f"}
LIMIAR_TEMPO = 1.15
PARES = [("gpt-4o", "llama3 (8B)"), ("gpt-4o", "llama3.2 (3B)"), ("llama3 (8B)", "llama3.2 (3B)")]
COL_OTIM = ["otimizada (custo)", "otimizada E tempo >= 1,15", "tempo >= 1,15 (so tempo)"]
PRESSUPOSTOS = {
    "C0": "partida fria: o modelo recebe apenas a consulta, sem esquema, sem estatisticas e sem memoria de execucoes anteriores",
    "C1": "o modelo recebe a consulta mais o esquema das tabelas e o numero de linhas de cada uma",
    "C2": "o modelo recebe, alem do esquema e dos tamanhos, um catalogo de transformacoes classicas de reescrita",
    "C3": "o modelo recebe, alem de tudo isso, o plano de execucao estimado da consulta original",
}


# ---------- carga ----------

def carregar(db):
    """Devolve (conjunto final, variante de esquema completo) do banco pedido."""
    os.environ["POSTGRES_DB"] = db
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM resultado WHERE run_id LIKE 'v3-%'"), conn)
    engine.dispose()
    df["modelo"] = df["modelo"].map(MODELOS).fillna(df["modelo"])
    df["rodada"] = df["run_id"].str.extract(r"-r(\d)")[0].fillna("1").astype(int)
    df["run_base"] = df["run_id"].str.replace(r"^v3-", "", regex=True)
    c0 = df[(df["config"] == "C0") & df["run_base"].str.contains("limpo")]
    c123 = df[(df["config"] != "C0") & df["run_base"].str.contains("stats")]
    variante = df[df["run_base"].str.contains("fmt-completo")]
    return pd.concat([c0, c123], ignore_index=True), variante.reset_index(drop=True)


def classificar(df):
    d = df.copy()
    v1 = d["v1_ok"].fillna(False).astype(bool)
    v2 = d["v2_ok"].fillna(False).astype(bool)
    medido = d["custo_reescrita"].notna() & d["custo_original"].notna() & d["razao_mediana"].notna()
    cat = pd.Series("invalida_sintaxe", index=d.index)
    cat[d["decisao"] == "rejeitada_semantica"] = "invalida_resultado"
    cat[d["decisao"] == "rejeitada_sem_mudanca"] = "sem_mudanca"
    valida = v1 & v2 & medido & (d["decisao"] != "rejeitada_sem_mudanca")
    cat[valida & (d["custo_reescrita"] >= d["custo_original"])] = "valida_sem_ganho"
    cat[valida & (d["custo_reescrita"] < d["custo_original"])] = "otimizada"
    d["categoria5"] = pd.Categorical(cat, CATS)
    d["erro_execucao"] = d["decisao"] == "erro"
    d["tempo_ok"] = medido & (d["razao_mediana"] >= LIMIAR_TEMPO)
    d["otimizada_e_tempo"] = (d["categoria5"] == "otimizada") & d["tempo_ok"]
    d["ganho_custo"] = np.where(medido, d["custo_original"] / d["custo_reescrita"].replace(0, np.nan), np.nan)
    return d


# ---------- tabelas ----------

def ordenar(g, chaves=("modelo", "config")):
    g["modelo"] = pd.Categorical(g["modelo"], ORDEM)
    return g.sort_values(list(chaves)).reset_index(drop=True)


def tabela_categorias(d, de):
    """Cinco categorias somadas nas tres repeticoes."""
    g = d.groupby(["modelo", "config", "categoria5"], observed=False).size().unstack("categoria5").reindex(columns=CATS).fillna(0).astype(int)
    g["n"] = g.sum(axis=1)
    g["erros_execucao (dentro de invalida_sintaxe)"] = d.groupby(["modelo", "config"])["erro_execucao"].sum().reindex(g.index).astype(int)
    g = ordenar(g.reset_index())
    g["de"] = de * 3
    return g


def tabela_categorias_media(d, de):
    """Cinco categorias na media das tres repeticoes."""
    g = d.groupby(["modelo", "config", "rodada", "categoria5"], observed=False).size().unstack("categoria5").reindex(columns=CATS).fillna(0)
    g = ordenar(g.groupby(level=[0, 1]).mean().round(1).reset_index())
    g["de"] = de
    return g


def tabela_otimizada(d, de):
    """Otimizadas por custo, por custo e tempo, e so por tempo (media das repeticoes)."""
    g = d.groupby(["modelo", "config", "rodada"]).agg(a=("categoria5", lambda s: int((s == "otimizada").sum())),
                                                      b=("otimizada_e_tempo", "sum"), c=("tempo_ok", "sum"))
    m = g.groupby(level=[0, 1]).mean().round(1)
    m.columns = COL_OTIM
    m = m.reset_index()
    m["modelo"] = pd.Categorical(m["modelo"], ORDEM)
    m["de"] = de
    return m.sort_values(["modelo", "config"]).reset_index(drop=True)


def ganho_custo(d):
    o = d[d["categoria5"] == "otimizada"]
    g = o.groupby(["modelo", "config"])["ganho_custo"].agg(n="count", mediana="median", p25=lambda s: s.quantile(.25),
                                                            p75=lambda s: s.quantile(.75), maximo="max").round(2).reset_index()
    return ordenar(g)


def cobertura_otimizaveis(d):
    """Quais das consultas otimizaveis (todas menos as de correcao) cada modelo otimizou."""
    ot = d[~d["query_id"].str.startswith("correcao")]
    linhas = []
    for q in sorted(ot["query_id"].unique()):
        r = {"consulta": q}
        for m in ORDEM:
            g = ot[(ot["query_id"] == q) & (ot["modelo"] == m)]
            por_fase = g.groupby("config")["categoria5"].apply(lambda x: int((x == "otimizada").sum()))
            r[m] = "3/3" if (por_fase == 3).any() else ("sim" if (por_fase > 0).any() else "-")
        linhas.append(r)
    t = pd.DataFrame(linhas)
    total = {"consulta": "total (de %d)" % len(t)}
    for m in ORDEM:
        total[m] = "%d em >= 1 rep.; %d nas 3 rep." % (int((t[m] != "-").sum()), int((t[m] == "3/3").sum()))
    return pd.concat([t, pd.DataFrame([total])], ignore_index=True)


def ganho_custo_por_consulta(d):
    o = d[d["categoria5"] == "otimizada"]
    g = o.groupby(["query_id", "modelo"])["ganho_custo"].median().unstack("modelo").reindex(columns=ORDEM).round(2)
    g["n_modelos"] = g.notna().sum(axis=1)
    g["max/min entre modelos"] = (g[ORDEM].max(axis=1) / g[ORDEM].min(axis=1)).round(2)
    return g.reset_index()


def categoria_c1(d):
    """Otimizadas por categoria de consulta na fase C1 (3 consultas x 3 repeticoes, de 9)."""
    o = d[(d["config"] == "C1") & (d["categoria5"] == "otimizada")].copy()
    o["cat"] = o["query_id"].str.rsplit("_", n=1).str[0]
    g = o.groupby(["cat", "modelo"]).size().unstack("modelo").reindex(columns=ORDEM).fillna(0).astype(int)
    return g.reset_index()


def compacto_vs_completo(d, variante):
    """Otimizadas em C1 com esquema compacto (media de 3 repeticoes) e com esquema completo (1 repeticao)."""
    compacto = tabela_otimizada(d, 18)
    compacto = compacto[compacto["config"] == "C1"].set_index("modelo")[COL_OTIM[0]]
    completo = variante.groupby("modelo")["categoria5"].apply(lambda s: int((s == "otimizada").sum()))
    g = pd.DataFrame({"compacto_otimizada_media": compacto, "completo_otimizada": completo}).reindex(ORDEM)
    return g.reset_index().rename(columns={"index": "modelo"})


def binomial_bicaudal(k, n):
    if n == 0:
        return float("nan")
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n)


def teste_sinais(d):
    """Por consulta, quantas execucoes cada modelo otimizou; conta em quantas consultas um supera o outro."""
    x = d.assign(ok=(d["categoria5"] == "otimizada").astype(int))
    por = x.groupby(["modelo", "config", "query_id"])["ok"].sum().unstack("modelo")
    total = por.groupby(level="query_id").sum()
    linhas = []
    for escopo, tab in [("C1", por.xs("C1", level="config")), ("total (4 niveis)", total)]:
        for a, b in PARES:
            diff = tab[a] - tab[b]
            mais, menos, emp = int((diff > 0).sum()), int((diff < 0).sum()), int((diff == 0).sum())
            n = mais + menos
            linhas.append({"escopo": escopo, "comparacao": f"{a} x {b}", "A > B": mais, "A < B": menos, "empates": emp,
                           "p-valor (sinais, bicaudal)": round(binomial_bicaudal(mais, n), 4) if n else float("nan"),
                           "soma A": int(tab[a].sum()), "soma B": int(tab[b].sum())})
    return pd.DataFrame(linhas)


def holm(ts):
    """Correcao de Holm para as tres comparacoes planejadas (total das quatro fases); C1 e exploratoria."""
    t = ts[ts["escopo"] != "C1"][["comparacao", "p-valor (sinais, bicaudal)"]].rename(columns={"p-valor (sinais, bicaudal)": "p"})
    t = t.sort_values("p").reset_index(drop=True)
    m = len(t)
    ajustado, maior = [], 0.0
    for i, p in enumerate(t["p"]):
        maior = max(maior, min(1.0, p * (m - i)))
        ajustado.append(round(maior, 4))
    t["p ajustado (Holm)"] = ajustado
    t["significativo a 5% apos Holm"] = t["p ajustado (Holm)"] < 0.05
    return t


def custo_igual_tempo_ganha(d):
    """Execucoes validas sem ganho de custo em que o tempo passou de 1,15."""
    x = d[(d["categoria5"] == "valida_sem_ganho") & d["tempo_ok"]]
    g = x.groupby(["modelo", "config", "query_id"]).agg(rodadas=("razao_mediana", "count"), razao_tempo_min=("razao_mediana", "min"),
                                                         razao_tempo_max=("razao_mediana", "max"), custo_orig=("custo_original", "first"),
                                                         custo_re=("custo_reescrita", "first")).round(2).reset_index()
    return ordenar(g, ("modelo", "config", "query_id"))


def ranking(d):
    """Ordem dos modelos por fase sob custo, custo e tempo, e so tempo."""
    t = tabela_otimizada(d, 18)
    linhas = []
    for cfg in NIVEIS + ["total"]:
        if cfg == "total":
            sub = t.groupby("modelo", observed=True)[COL_OTIM].sum()
        else:
            sub = t[t["config"] == cfg].set_index("modelo")
        ordens = {c: " > ".join(sub[c].sort_values(ascending=False).index.astype(str)) for c in COL_OTIM}
        linhas.append({"nivel": cfg, **ordens, "mesma ordem custo x tempo1,15": ordens[COL_OTIM[0]] == ordens[COL_OTIM[2]]})
    return pd.DataFrame(linhas)


def sintese(d):
    g = d.groupby("modelo").agg(
        n=("categoria5", "count"),
        melhorou_otimizada=("categoria5", lambda s: int((s == "otimizada").sum())),
        nao_melhorou_nao_quebrou=("categoria5", lambda s: int(s.isin(["sem_mudanca", "valida_sem_ganho"]).sum())),
        invalidou_resultado=("categoria5", lambda s: int((s == "invalida_resultado").sum())),
        nao_executa=("categoria5", lambda s: int((s == "invalida_sintaxe").sum()))).reset_index()
    for c in ["melhorou_otimizada", "nao_melhorou_nao_quebrou", "invalidou_resultado", "nao_executa"]:
        g[c + " %"] = (100 * g[c] / g["n"]).round(0).astype(int)
    return ordenar(g, ("modelo",))


# ---------- saida ----------

def md(df, fmt="{:.2f}"):
    """Tabela em Markdown."""
    cols = list(df.columns)
    linhas = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r[c]
            vals.append(("" if np.isnan(v) else fmt.format(v)) if isinstance(v, float) else str(v))
        linhas.append("| " + " | ".join(vals) + " |")
    return "\n".join(linhas)


def figura(media, caminho, de):
    """Quatro paineis (uma fase cada) com barras empilhadas por modelo."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, eixos = plt.subplots(1, 4, figsize=(6.3, 3.1), sharey=True)
    for eixo, cfg in zip(eixos, NIVEIS):
        sub = media[media["config"] == cfg].set_index("modelo").reindex(ORDEM)
        base = np.zeros(3)
        for c in CATS:
            eixo.bar(range(3), sub[c].values, bottom=base, color=CORES[c], label=ROTULOS[c], width=0.65)
            base = base + sub[c].values
        eixo.set_xticks(range(3))
        eixo.set_xticklabels(["3B", "8B", "GPT-4o"], fontsize=9)
        eixo.tick_params(axis="y", labelsize=9)
        eixo.set_title(f"Fase {cfg}", fontsize=10)
        eixo.set_ylim(0, de)
        eixo.spines[["top", "right"]].set_visible(False)
    eixos[0].set_ylabel(f"consultas, de {de}\n(média de 3 repetições)", fontsize=9)
    alcas, nomes = eixos[0].get_legend_handles_labels()
    fig.legend(alcas, nomes, loc="lower center", ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    fig.savefig(caminho, dpi=300, bbox_inches="tight")
    plt.close(fig)


def salvar(nome, tabela):
    tabela.to_csv(SAIDA / f"{nome}.csv", index=False)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    texto = ["# Conjunto final: cinco categorias por execucao, custo estimado como criterio de ganho", "",
             "Media = media das tres repeticoes; soma = soma das tres. Erros de execucao (estouro de 5 min ou de disco) "
             "contam em `invalida_sintaxe`.", ""]
    for db, rotulo, figura_nome, de in [("tpch", "Cenario 1: TPC-H", "fig_tpch.png", 4),
                                        ("tcc", "Cenario 2: base controlada", "fig_controlada.png", 18)]:
        final, variante = carregar(db)
        d = classificar(final)
        salvar(f"{db}_execucoes_classificadas", d)
        soma, media, otim = tabela_categorias(d, de), tabela_categorias_media(d, de), tabela_otimizada(d, de)
        salvar(f"{db}_categorias_soma", soma)
        salvar(f"{db}_categorias_media", media)
        salvar(f"{db}_otimizada_vs_tempo", otim)
        salvar(f"{db}_custo_igual_tempo_ganha", custo_igual_tempo_ganha(d))
        salvar(f"{db}_sintese", sintese(d))
        figura(media, SAIDA / figura_nome, de)

        texto += [f"## {rotulo} ({len(d)} execucoes)", ""]
        for cfg in NIVEIS:
            texto += [f"### Fase {cfg}", "", f"Pressuposto: {PRESSUPOSTOS[cfg]}.", "",
                      md(media[media["config"] == cfg].drop(columns=["config"]), "{:.1f}"), ""]
        texto += [f"![{rotulo}]({figura_nome})", "",
                  "### Cinco categorias, soma das 3 repeticoes", "", md(soma, "{:.0f}"), "",
                  "### Otimizada (custo) x otimizada e tempo >= 1,15 x so tempo (media de 3 repeticoes)", "", md(otim, "{:.1f}"), "",
                  "### Execucoes validas com custo igual ou maior e tempo >= 1,15", "",
                  md(custo_igual_tempo_ganha(d)) if len(custo_igual_tempo_ganha(d)) else "_nenhuma_", "",
                  "### Sintese: melhorou / nao melhorou mas nao quebrou / invalidou / nao executa", "", md(sintese(d), "{:.0f}"), ""]

        if db == "tcc":
            # Tabelas que so fazem sentido onde houve otimizacao.
            partes = {"ganho_custo": ganho_custo(d), "ganho_custo_por_consulta": ganho_custo_por_consulta(d),
                      "cobertura_otimizaveis": cobertura_otimizaveis(d), "categoria_C1_custo": categoria_c1(d),
                      "teste_sinais_custo": teste_sinais(d), "teste_sinais_holm": holm(teste_sinais(d)), "ranking": ranking(d),
                      "compacto_vs_completo_custo": compacto_vs_completo(d, classificar(variante))}
            for nome, tabela in partes.items():
                salvar(f"{db}_{nome}", tabela)
            texto += ["### Ganho de custo das otimizadas (custo original / custo da reescrita)", "", md(partes["ganho_custo"]), "",
                      "### Ganho de custo por consulta e modelo (mediana das execucoes otimizadas)", "", md(partes["ganho_custo_por_consulta"]), "",
                      "### Cobertura das consultas otimizaveis: '3/3' = otimizada nas 3 repeticoes de alguma fase", "", md(partes["cobertura_otimizaveis"]), "",
                      "### Otimizadas por categoria na fase C1 (de 9)", "", md(partes["categoria_C1_custo"]), "",
                      "### Teste de sinais pareado por consulta", "", md(partes["teste_sinais_custo"], "{:.4f}"), "",
                      "### Correcao de Holm nas tres comparacoes planejadas (total das fases)", "", md(partes["teste_sinais_holm"], "{:.4f}"), "",
                      "### Ordem entre modelos por fase: custo x custo e tempo x so tempo", "", md(partes["ranking"]), "",
                      "### Esquema compacto x completo na fase C1", "", md(partes["compacto_vs_completo_custo"], "{:.1f}"), ""]
    (SAIDA / "tabelas.md").write_text("\n".join(texto) + "\n", encoding="utf-8")
    print("\n".join(texto))


if __name__ == "__main__":
    main()
