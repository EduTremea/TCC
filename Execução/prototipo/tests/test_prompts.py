"""Testes dos builders de prompt C0-C3 (puros, sem banco)."""
from __future__ import annotations

import pytest

from src.prompts.contexto import Nivel, montar_prompt

SQL = "SELECT 1"
ESQUEMA = "cliente(id integer, nome text)"
PLANO = "Seq Scan on cliente (cost=0.00..1.00 rows=1)"
TRABALHOS_PROIBIDOS = ["LLM-R2", "R-Bot", "QUITE", "LITHE", "ReSequel"]


def test_c0_contem_so_a_consulta():
    p = montar_prompt(Nivel.C0, SQL)
    assert SQL in p
    assert ESQUEMA not in p
    assert "Tecnicas de reescrita" not in p


def test_c1_inclui_esquema_e_estatisticas():
    p = montar_prompt(Nivel.C1, SQL, esquema=ESQUEMA, estatisticas="cliente: 5000 linhas")
    assert ESQUEMA in p
    assert "5000 linhas" in p
    assert "Tecnicas de reescrita" not in p


def test_c2_inclui_catalogo():
    p = montar_prompt(Nivel.C2, SQL, esquema=ESQUEMA)
    assert "Tecnicas de reescrita" in p
    assert "sargaveis" in p.lower()
    assert PLANO not in p


def test_c3_inclui_plano_e_exige_plano():
    with pytest.raises(ValueError):
        montar_prompt(Nivel.C3, SQL, esquema=ESQUEMA)
    p = montar_prompt(Nivel.C3, SQL, esquema=ESQUEMA, plano=PLANO)
    assert PLANO in p
    assert "Tecnicas de reescrita" in p


def test_c1_exige_esquema():
    with pytest.raises(ValueError):
        montar_prompt(Nivel.C1, SQL)


def test_guardrail_sem_referencia_a_trabalhos():
    for nivel in Nivel:
        p = montar_prompt(nivel, SQL, esquema=ESQUEMA, estatisticas="x", plano=PLANO)
        for termo in TRABALHOS_PROIBIDOS:
            assert termo not in p, f"{nivel.value} vazou referencia a {termo}"
