"""Modelo local pelo Ollama. Roda em CPU, sem acesso a rede durante a inferencia."""
import os
import re
import subprocess

import ollama


def extrair_sql(resposta):
    """Tira cercas de codigo e texto em volta, caso o modelo devolva mais que o SQL."""
    bloco = re.search(r"```(?:sql)?\s*(.*?)```", resposta, re.DOTALL | re.IGNORECASE)
    if bloco:
        return bloco.group(1).strip()
    return resposta.strip()


class OllamaClient:
    def __init__(self, model=None, host=None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
        self._client = ollama.Client(host=host or os.getenv("OLLAMA_HOST"))

    def reescrever(self, prompt):
        # Cada chamada e independente: sem "context", sem sessao, temperatura zero.
        resposta = self._client.generate(model=self.model, prompt=prompt, options={"temperature": 0})
        return extrair_sql(resposta["response"])


def descarregar_modelos():
    """Tira da memoria qualquer modelo carregado no Ollama e diz como ficou."""
    try:
        saida = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"ollama indisponivel: {exc}"
    for linha in saida.strip().splitlines()[1:]:
        if linha.strip():
            subprocess.run(["ollama", "stop", linha.split()[0]], capture_output=True, text=True, timeout=60)
    try:
        saida = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"ollama indisponivel: {exc}"
    restantes = [l for l in saida.strip().splitlines()[1:] if l.strip()]
    if restantes:
        return "ollama ainda com modelo: " + "; ".join(restantes)
    return "ollama ps vazio"
