"""Uma execucao: uma consulta, uma fase de contexto, um modelo.

O modelo so propoe. Aqui ficam as verificacoes que nao dependem de tempo:
reescrita identica, sintaxe (V1), resultado (V2) e custo estimado. A medicao
de tempo acontece depois, em lote, com nenhum modelo carregado (remedir_v3.py).
"""
import hashlib
import time

from ..prompts.contexto import Nivel, montar_prompt
from ..validation.desempenho import custo_estimado, mesma_consulta
from ..validation.semantica import mesma_semantica
from ..validation.sintatica import valida_sintaxe
from . import introspec


def executar_celula(engine, modelo, run_id, benchmark, query_id, sql, nivel):
    esquema = introspec.esquema_texto(engine)
    estatisticas = introspec.estatisticas_texto(engine)
    if nivel != Nivel.C0 and "~ 0 linhas" in estatisticas:
        # Tabela "vazia" no prompt e estatistica quebrada, nao dado. Para o lote.
        raise RuntimeError("estatisticas zeradas; rode ANALYZE antes do lote:\n" + estatisticas)
    plano = introspec.plano_texto(engine, sql) if nivel == Nivel.C3 else None
    prompt = montar_prompt(nivel, sql, esquema=esquema, estatisticas=estatisticas, plano=plano)

    linha = {
        "run_id": run_id,
        "benchmark": benchmark,
        "query_id": query_id,
        "config": nivel.value,
        "modelo": modelo.model,
        "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
        "prompt": prompt,
        "sql_original": sql,
        "sql_reescrita": None,
        "v1_ok": None,
        "v2_ok": None,
        "custo_original": None,
        "custo_reescrita": None,
        "tempo_llm_ms": None,
        "decisao": "erro",
        "erro": None,
    }
    try:
        inicio = time.perf_counter()
        reescrita = modelo.reescrever(prompt)
        linha["tempo_llm_ms"] = (time.perf_counter() - inicio) * 1000
        linha["sql_reescrita"] = reescrita

        if mesma_consulta(sql, reescrita):
            linha.update(v1_ok=True, v2_ok=True, decisao="rejeitada_sem_mudanca")
            return linha

        ok, erro = valida_sintaxe(engine, reescrita)
        linha["v1_ok"] = ok
        if not ok:
            linha.update(decisao="rejeitada_sintaxe", erro=erro)
            return linha

        linha["v2_ok"] = mesma_semantica(engine, sql, reescrita)
        if not linha["v2_ok"]:
            linha["decisao"] = "rejeitada_semantica"
            return linha

        linha["custo_original"] = custo_estimado(engine, sql)
        linha["custo_reescrita"] = custo_estimado(engine, reescrita)
        linha["decisao"] = "pendente_medicao"
    except Exception as exc:
        linha.update(decisao="erro", erro=str(exc)[:500])
    return linha
