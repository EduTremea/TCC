"""Monta o prompt de cada fase de contexto.

C0: so a consulta.  C1: + esquema e numero de linhas.  C2: + catalogo de
transformacoes.  C3: + plano EXPLAIN da consulta original.
Todo o contexto sai do proprio banco; nenhum trabalho de referencia e citado.
"""
from enum import Enum

from .transformacoes import catalogo_texto


class Nivel(str, Enum):
    C0 = "C0"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


INSTRUCAO = (
    "Voce reescreve consultas SQL para PostgreSQL.\n"
    "Reescreva a consulta a seguir mantendo exatamente o mesmo resultado, porem "
    "de forma mais eficiente.\n"
    "Responda APENAS com a consulta SQL reescrita, sem explicacao e sem markdown."
)


def montar_prompt(nivel, sql, esquema=None, estatisticas=None, plano=None):
    if nivel != Nivel.C0 and not esquema:
        raise ValueError(f"{nivel.value}: 'esquema' e obrigatorio.")
    if nivel == Nivel.C3 and not plano:
        raise ValueError("C3: 'plano' (EXPLAIN) e obrigatorio.")

    partes = [INSTRUCAO, ""]
    if nivel != Nivel.C0:
        partes += ["Esquema do banco:", esquema, ""]
        if estatisticas:
            partes += ["Estatisticas das tabelas:", estatisticas, ""]
    if nivel in (Nivel.C2, Nivel.C3):
        partes += ["Tecnicas de reescrita a considerar:", catalogo_texto(), ""]
    if nivel == Nivel.C3:
        partes += ["Plano de execucao da consulta original (EXPLAIN):", plano, ""]
    partes += ["Consulta original:", sql]
    return "\n".join(partes)
