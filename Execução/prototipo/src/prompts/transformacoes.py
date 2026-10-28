"""Catalogo de transformacoes classicas de reescrita (contexto do nivel C2).

Guardrail de contaminacao: as descricoes sao genericas e NAO citam nenhum
trabalho de referencia (LLM-R2, R-Bot, QUITE, LITHE, ReSequel). Todo o conteudo
vem de conhecimento classico de otimizacao de consultas.
"""
from __future__ import annotations

CATALOGO: list[str] = [
    "Troque subconsultas correlacionadas por juncoes equivalentes quando o resultado for preservado.",
    "Prefira predicados sargaveis: nao aplique funcoes sobre a coluna filtrada; use faixas com >= e <.",
    "Remova DISTINCT quando as colunas projetadas ja forem unicas (por exemplo, uma chave primaria).",
    "Elimine subconsultas e juncoes que nao alteram o conjunto de resultados.",
    "Use CTEs (WITH) para evitar recomputar a mesma subconsulta varias vezes.",
    "Substitua agregacoes escalares calculadas por linha por uma unica agregacao com GROUP BY.",
    "Simplifique predicados e aplique os filtros o mais cedo possivel.",
    "Ao converter NOT IN em anti-juncao, atente para valores NULL, que alteram o resultado.",
]


def catalogo_texto() -> str:
    """Devolve o catalogo formatado como lista de marcadores."""
    return "\n".join(f"- {t}" for t in CATALOGO)
