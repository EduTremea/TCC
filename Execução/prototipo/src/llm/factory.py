"""Escolhe o modelo pela variavel LLM_PROVIDER: "ollama" (padrao) ou "openai"."""
import os

from .ollama_client import OllamaClient


def escolher_modelo():
    if os.getenv("LLM_PROVIDER", "ollama").lower() == "openai":
        from .openai_client import OpenAIClient
        return OpenAIClient()
    return OllamaClient()
