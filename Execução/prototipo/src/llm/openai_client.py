"""Modelo pago pela API da OpenAI. Uma unica mensagem por chamada, sem ferramentas e sem busca."""
import os

from openai import OpenAI

from .ollama_client import extrair_sql


class OpenAIClient:
    def __init__(self, model=None, api_key=None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        chave = api_key or os.getenv("OPENAI_API_KEY")
        if not chave:
            raise RuntimeError("OPENAI_API_KEY nao definida; preencha o .env")
        self._client = OpenAI(api_key=chave)

    def reescrever(self, prompt):
        resposta = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return extrair_sql(resposta.choices[0].message.content or "")
