"""Cada execucao vira uma linha na tabela `resultado`, com o prompt completo para auditoria."""
from sqlalchemy import text

DDL = """
CREATE TABLE IF NOT EXISTS resultado (
    id                 serial PRIMARY KEY,
    run_id             text NOT NULL,
    benchmark          text NOT NULL,
    query_id           text NOT NULL,
    config             text NOT NULL,
    modelo             text NOT NULL,
    prompt_hash        text NOT NULL,
    prompt             text NOT NULL,
    sql_original       text NOT NULL,
    sql_reescrita      text,
    v1_ok              boolean,
    v2_ok              boolean,
    custo_original     double precision,
    custo_reescrita    double precision,
    tempo_original_ms  double precision,
    tempo_reescrita_ms double precision,
    tempo_llm_ms       double precision,
    linhas_original    double precision,
    linhas_reescrita   double precision,
    razao_mediana      double precision,
    protocolo          text,
    decisao            text NOT NULL,
    erro               text,
    criado_em          timestamptz NOT NULL DEFAULT now()
);
"""

# Tabelas criadas por versoes anteriores nao tinham estas colunas.
COLUNAS_NOVAS = ["linhas_original double precision", "linhas_reescrita double precision",
                 "razao_mediana double precision", "protocolo text"]

CAMPOS = [
    "run_id", "benchmark", "query_id", "config", "modelo", "prompt_hash",
    "prompt", "sql_original", "sql_reescrita", "v1_ok", "v2_ok",
    "custo_original", "custo_reescrita", "tempo_original_ms",
    "tempo_reescrita_ms", "tempo_llm_ms", "linhas_original", "linhas_reescrita",
    "decisao", "erro", "razao_mediana", "protocolo",
]


def criar_tabela(engine):
    with engine.begin() as conn:
        conn.execute(text(DDL))
        for coluna in COLUNAS_NOVAS:
            conn.execute(text(f"ALTER TABLE resultado ADD COLUMN IF NOT EXISTS {coluna}"))


def gravar(engine, linha):
    sql = text(f"INSERT INTO resultado ({', '.join(CAMPOS)}) VALUES ({', '.join(':' + c for c in CAMPOS)})")
    with engine.begin() as conn:
        conn.execute(sql, {c: linha.get(c) for c in CAMPOS})
