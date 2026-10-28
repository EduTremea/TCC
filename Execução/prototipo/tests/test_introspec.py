"""Testes do formatador de esquema (puro, sem banco)."""
from __future__ import annotations

import pytest

from src.experimento.introspec import formatar_esquema

COLUNAS = [
    ("cliente", "id", "integer", False),
    ("cliente", "nome", "text", False),
    ("pedido", "id", "integer", False),
    ("pedido", "cliente_id", "integer", False),
    ("pedido", "cupom_id", "integer", True),
]
RESTRICOES = {
    "cliente": ["PRIMARY KEY (id)"],
    "pedido": ["PRIMARY KEY (id)", "FOREIGN KEY (cliente_id) REFERENCES cliente(id)"],
}
INDICES = {"pedido": ["idx_pedido_cliente (cliente_id)"]}


def test_compacto_uma_linha_por_tabela():
    texto = formatar_esquema(COLUNAS, "compacto")
    assert texto.splitlines() == [
        "cliente(id integer, nome text)",
        "pedido(id integer, cliente_id integer, cupom_id integer)",
    ]


def test_completo_traz_null_chaves_e_indices():
    texto = formatar_esquema(COLUNAS, "completo", RESTRICOES, INDICES)
    assert "tabela pedido:" in texto
    assert "  cliente_id integer NOT NULL" in texto
    assert "  cupom_id integer\n" in texto + "\n"  # aceita NULL: sem marcador
    assert "FOREIGN KEY (cliente_id) REFERENCES cliente(id)" in texto
    assert "INDEX idx_pedido_cliente (cliente_id)" in texto


def test_completo_nao_mistura_tabelas():
    texto = formatar_esquema(COLUNAS, "completo", RESTRICOES, INDICES)
    bloco_cliente = texto.split("tabela pedido:")[0]
    assert "INDEX" not in bloco_cliente
    assert "FOREIGN KEY" not in bloco_cliente


def test_formato_invalido():
    with pytest.raises(ValueError):
        formatar_esquema(COLUNAS, "json")
