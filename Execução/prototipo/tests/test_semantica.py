"""Testes da comparacao semantica que independem de banco em execucao."""
import pandas as pd

from src.validation.semantica import _normaliza


def test_normaliza_ignora_ordem_de_linhas():
    a = pd.DataFrame({"id": [1, 2, 3], "v": ["a", "b", "c"]})
    b = pd.DataFrame({"id": [3, 1, 2], "v": ["c", "a", "b"]})
    assert _normaliza(a).equals(_normaliza(b))


def test_normaliza_ignora_ordem_de_colunas():
    a = pd.DataFrame({"id": [1, 2], "v": ["a", "b"]})
    b = pd.DataFrame({"v": ["a", "b"], "id": [1, 2]})
    assert _normaliza(a).equals(_normaliza(b))


def test_normaliza_detecta_diferenca_real():
    a = pd.DataFrame({"id": [1, 2], "v": ["a", "b"]})
    b = pd.DataFrame({"id": [1, 2], "v": ["a", "X"]})
    assert not _normaliza(a).equals(_normaliza(b))
