"""Contexto extraido do proprio banco: esquema, numero de linhas e plano.

ESQUEMA_FORMATO escolhe o formato do esquema: "compacto" (padrao), uma linha
por tabela, ou "completo", com NOT NULL, chaves e indices.
"""
import os

from sqlalchemy import text

FORMATOS = ("compacto", "completo")
TABELAS_INTERNAS = ["resultado"]  # tabela do proprio experimento; nao faz parte da base avaliada


def formato_padrao():
    formato = os.getenv("ESQUEMA_FORMATO", "compacto").strip().lower()
    if formato not in FORMATOS:
        raise ValueError(f"ESQUEMA_FORMATO invalido: {formato!r}; use um de {FORMATOS}")
    return formato


def _consultar(engine, sql):
    with engine.connect() as conn:
        return conn.execute(text(sql), {"internas": TABELAS_INTERNAS}).fetchall()


def _colunas(engine):
    """(tabela, coluna, tipo, aceita_null) das tabelas de dados do schema public."""
    return [tuple(r) for r in _consultar(engine, """
        SELECT c.table_name, c.column_name, c.data_type, c.is_nullable = 'YES'
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON t.table_schema = c.table_schema AND t.table_name = c.table_name
        WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
          AND c.table_name <> ALL(:internas)
        ORDER BY c.table_name, c.ordinal_position
    """)]


def _restricoes(engine):
    """Chaves primarias, estrangeiras e UNIQUE por tabela."""
    saida = {}
    for tabela, definicao in _consultar(engine, """
        SELECT cl.relname, pg_get_constraintdef(co.oid)
        FROM pg_constraint co
        JOIN pg_class cl ON cl.oid = co.conrelid
        JOIN pg_namespace n ON n.oid = cl.relnamespace
        WHERE n.nspname = 'public' AND co.contype IN ('p', 'f', 'u')
          AND cl.relname <> ALL(:internas)
        ORDER BY cl.relname, co.contype DESC, co.conname
    """):
        saida.setdefault(tabela, []).append(definicao)
    return saida


def _indices(engine):
    """Indices que nao sao de chave, por tabela: nome(colunas)."""
    saida = {}
    for tabela, nome, definicao in _consultar(engine, """
        SELECT i.tablename, i.indexname, i.indexdef
        FROM pg_indexes i
        LEFT JOIN pg_constraint co ON co.conname = i.indexname
        WHERE i.schemaname = 'public' AND co.oid IS NULL
          AND i.tablename <> ALL(:internas)
        ORDER BY i.tablename, i.indexname
    """):
        colunas = definicao[definicao.index("("):] if "(" in definicao else ""
        saida.setdefault(tabela, []).append(f"{nome}{colunas}")
    return saida


def formatar_esquema(colunas, formato="compacto", restricoes=None, indices=None):
    """Monta o texto do esquema a partir das linhas do catalogo."""
    if formato not in FORMATOS:
        raise ValueError(f"formato invalido: {formato!r}")
    tabelas = {}
    for tabela, coluna, tipo, aceita_null in colunas:
        tabelas.setdefault(tabela, []).append((coluna, tipo, aceita_null))

    if formato == "compacto":
        return "\n".join(f"{t}({', '.join(f'{c} {tp}' for c, tp, _ in cols)})" for t, cols in tabelas.items())

    blocos = []
    for t, cols in tabelas.items():
        linhas = [f"tabela {t}:"]
        linhas += [f"  {c} {tp}{'' if aceita_null else ' NOT NULL'}" for c, tp, aceita_null in cols]
        linhas += [f"  {d}" for d in (restricoes or {}).get(t, [])]
        linhas += [f"  INDEX {d}" for d in (indices or {}).get(t, [])]
        blocos.append("\n".join(linhas))
    return "\n\n".join(blocos)


def esquema_texto(engine, formato=None):
    formato = formato or formato_padrao()
    colunas = _colunas(engine)
    if formato == "compacto":
        return formatar_esquema(colunas, "compacto")
    return formatar_esquema(colunas, "completo", _restricoes(engine), _indices(engine))


def estatisticas_texto(engine):
    """Numero aproximado de linhas por tabela (reltuples, gravado pelo ANALYZE)."""
    linhas = []
    with engine.connect() as conn:
        tabelas = conn.execute(text("""
            SELECT c.relname, c.reltuples::bigint
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname <> ALL(:internas)
            ORDER BY c.relname
        """), {"internas": TABELAS_INTERNAS}).fetchall()
        for nome, estimativa in tabelas:
            if not estimativa or estimativa <= 0:
                estimativa = conn.execute(text(f'SELECT count(*) FROM "{nome}"')).scalar_one()
            linhas.append(f"{nome} ~ {estimativa} linhas")
    return "\n".join(linhas)


def plano_texto(engine, sql):
    """Saida do EXPLAIN (custo estimado) da consulta original, como texto."""
    with engine.connect() as conn:
        return "\n".join(r[0] for r in conn.execute(text(f"EXPLAIN {sql}")).fetchall())
