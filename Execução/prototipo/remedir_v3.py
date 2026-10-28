"""Mede o tempo das reescritas ja gravadas, com nenhum modelo carregado.

Uso:
    uv run python remedir_v3.py remedir <banco> <fases|-> <run_id> [run_id ...]
        Cada run_id de origem gera um "v3-<run_id>" com as mesmas reescritas.
        Reescrita igual a original: rejeitada_sem_mudanca, sem medir.
        Origem rejeitada em V1/V2 ou com erro: decisao copiada (o SQL e o mesmo).
        Demais: V1 e V2 refeitas e, se passarem, medicao intercalada.

    uv run python remedir_v3.py aa [rodadas]
        Teste da consulta contra ela mesma nas 18 consultas da base controlada.
        Serve para calibrar o limiar de tempo: uma consulta identica deve dar razao perto de 1.
"""
import hashlib
import os
import sys

from sqlalchemy import text

from rodar_lote import carregar_consultas
from src.db import get_engine
from src.experimento import persistencia
from src.llm.ollama_client import descarregar_modelos
from src.validation.desempenho import LIMIAR_TEMPO, PROTOCOLO, medir_intercalado, mesma_consulta
from src.validation.semantica import mesma_semantica
from src.validation.sintatica import valida_sintaxe

COLUNAS_ORIGEM = ("benchmark, query_id, config, modelo, prompt_hash, prompt, sql_original, sql_reescrita, "
                  "v1_ok, v2_ok, decisao, erro, tempo_llm_ms")
REJEITADAS_SEM_TEMPO = ("rejeitada_sintaxe", "rejeitada_semantica", "erro")


def nova_linha(**campos):
    linha = {c: None for c in persistencia.CAMPOS}
    linha.update(campos)
    return linha


def decisao_por_tempo(razao):
    return "aceita" if razao >= LIMIAR_TEMPO else "rejeitada_desempenho"


def validar_e_medir(engine, linha):
    """V1, V2 e medicao intercalada para uma linha que ja tem sql_original e sql_reescrita."""
    original, reescrita = linha["sql_original"], linha["sql_reescrita"]
    ok, erro = valida_sintaxe(engine, reescrita)
    linha["v1_ok"] = ok
    if not ok:
        linha.update(decisao="rejeitada_sintaxe", erro=erro)
        return linha
    try:
        linha["v2_ok"] = mesma_semantica(engine, original, reescrita)
    except Exception as exc:
        linha.update(decisao="erro", erro=str(exc)[:500], v2_ok=False)
        return linha
    if not linha["v2_ok"]:
        linha["decisao"] = "rejeitada_semantica"
        return linha
    medida = medir_intercalado(engine, original, reescrita)
    medida.pop("razoes")
    linha.update(medida, decisao=decisao_por_tempo(medida["razao_mediana"]))
    return linha


def remedir(engine, run_ids, fases):
    estado = descarregar_modelos()
    print("ollama:", estado, flush=True)
    for origem in run_ids:
        destino = f"v3-{origem}"
        with engine.connect() as conn:
            feitas = set(conn.execute(text("SELECT query_id || '|' || config FROM resultado WHERE run_id = :d"),
                                      {"d": destino}).scalars())
            linhas = conn.execute(text(f"SELECT {COLUNAS_ORIGEM} FROM resultado WHERE run_id = :r ORDER BY query_id, config"),
                                  {"r": origem}).mappings().all()
        if fases:
            linhas = [l for l in linhas if l["config"] in fases]
        print(f"origem={origem} destino={destino} linhas={len(linhas)} ja feitas={len(feitas)}", flush=True)
        for i, origem_linha in enumerate(linhas, 1):
            if f"{origem_linha['query_id']}|{origem_linha['config']}" in feitas:
                continue
            linha = nova_linha(**dict(origem_linha), run_id=destino, protocolo=f"{PROTOCOLO}; {estado}")
            if not origem_linha["sql_reescrita"]:
                linha.update(decisao="erro", erro=(origem_linha["erro"] or "sem reescrita")[:500])
            elif mesma_consulta(origem_linha["sql_original"], origem_linha["sql_reescrita"]):
                linha.update(decisao="rejeitada_sem_mudanca", v1_ok=True, v2_ok=True)
            elif origem_linha["decisao"] in REJEITADAS_SEM_TEMPO:
                linha["protocolo"] += "; decisao V1/V2 copiada da origem"
            else:
                linha.update(v1_ok=None, v2_ok=None, erro=None)
                try:
                    linha = validar_e_medir(engine, linha)
                except Exception as exc:
                    linha.update(decisao="erro", erro=str(exc)[:500])
            persistencia.gravar(engine, linha)
            razao = f"{linha['razao_mediana']:.2f}" if linha.get("razao_mediana") else "-"
            print(f"[{i:>3}/{len(linhas)}] {origem_linha['query_id']:<16} {origem_linha['config']} "
                  f"{linha['decisao']:<22} razao={razao}", flush=True)
        print(f"{destino} concluido", flush=True)


def teste_aa(engine, rodadas):
    estado = descarregar_modelos()
    print("ollama:", estado, flush=True)
    consultas = carregar_consultas("benchmarks/controlled/queries")
    for r in range(1, rodadas + 1):
        run_id = "aa-v3-controlada" if r == 1 else f"aa-v3-controlada-r{r}"
        razoes = []
        for query_id, sql in consultas:
            medida = medir_intercalado(engine, sql, sql)
            pares = medida.pop("razoes")
            linha = nova_linha(run_id=run_id, benchmark="controlled", query_id=query_id, config="AA-v3", modelo="nenhum",
                               prompt_hash=hashlib.sha256(sql.encode()).hexdigest()[:16], prompt="",
                               sql_original=sql, sql_reescrita=sql, v1_ok=True, v2_ok=True,
                               protocolo=f"{PROTOCOLO}; {estado}; A/A: original contra ela mesma",
                               decisao=decisao_por_tempo(medida["razao_mediana"]), **medida)
            persistencia.gravar(engine, linha)
            razoes.append(medida["razao_mediana"])
            print(f"[{run_id}] {query_id:<16} razao mediana {medida['razao_mediana']:.3f}  pares {[round(x, 2) for x in pares]}", flush=True)
        razoes.sort()
        acima = sum(1 for x in razoes if x >= LIMIAR_TEMPO)
        print(f"{run_id}: {acima} de {len(razoes)} acima de {LIMIAR_TEMPO}; "
              f"min/mediana/max = {razoes[0]:.3f}/{razoes[len(razoes) // 2]:.3f}/{razoes[-1]:.3f}", flush=True)


def main():
    args = sys.argv[1:]
    if args and args[0] == "aa":
        engine = get_engine()
        persistencia.criar_tabela(engine)
        teste_aa(engine, int(args[1]) if len(args) > 1 else 3)
    elif args and args[0] == "remedir" and len(args) >= 4:
        os.environ["POSTGRES_DB"] = args[1]
        fases = None if args[2] == "-" else args[2].split(",")
        engine = get_engine()
        persistencia.criar_tabela(engine)
        remedir(engine, args[3:], fases)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
