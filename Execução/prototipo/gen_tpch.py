"""Gera TPC-H (escala 1) usando o gerador oficial embutido no DuckDB.

Uso:
    uv run --with duckdb python gen_tpch.py

Produz:
  - data/tpch/<tabela>.csv  (8 tabelas, para carga via COPY no PostgreSQL)
  - benchmarks/tpch/queries/qNN.sql (as 22 consultas oficiais do TPC-H)

Nada e enviado para a internet alem do download unico da extensao tpch do DuckDB.
"""
from __future__ import annotations

import pathlib

import duckdb

ESCALA = 1
OUT = pathlib.Path("data/tpch")
QDIR = pathlib.Path("benchmarks/tpch/queries")
OUT.mkdir(parents=True, exist_ok=True)
QDIR.mkdir(parents=True, exist_ok=True)

TABELAS = ["region", "nation", "part", "supplier", "partsupp", "customer", "orders", "lineitem"]


def main() -> None:
    con = duckdb.connect()
    con.execute("INSTALL tpch; LOAD tpch;")
    print(f"gerando TPC-H sf={ESCALA} ...", flush=True)
    con.execute(f"CALL dbgen(sf={ESCALA})")

    for t in TABELAS:
        destino = (OUT / f"{t}.csv").as_posix()
        con.execute(f"COPY {t} TO '{destino}' (FORMAT csv, HEADER, DELIMITER ',')")
        n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} linhas -> {destino}", flush=True)

    consultas = con.execute(
        "SELECT query_nr, query FROM tpch_queries() ORDER BY query_nr"
    ).fetchall()
    for nr, q in consultas:
        (QDIR / f"q{nr:02d}.sql").write_text(q.strip() + "\n", encoding="utf-8")
    print(f"22 consultas gravadas em {QDIR} (total {len(consultas)})", flush=True)


if __name__ == "__main__":
    main()
