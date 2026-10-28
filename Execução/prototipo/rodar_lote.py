"""Roda um lote: todas as consultas de uma pasta, nas fases pedidas, com um modelo.

Uso:
    OLLAMA_MODEL=<modelo> [POSTGRES_DB=<banco>] uv run python rodar_lote.py <run_id> [pasta] [benchmark] [consultas] [fases]

    pasta       pasta com os .sql (padrao: benchmarks/controlled/queries)
    benchmark   rotulo gravado na coluna benchmark (padrao: controlled)
    consultas   nomes separados por virgula, ou "-" para todas
    fases       ex.: C1,C2,C3 (padrao: C0,C1,C2,C3)

    LLM_PROVIDER=openai usa o modelo pago; ESQUEMA_FORMATO=completo muda o formato do esquema.

Exemplo:
    OLLAMA_MODEL=llama3 POSTGRES_DB=tpch uv run python rodar_lote.py tpch-llama3 benchmarks/tpch/queries tpch q03,q04,q06,q18

O tempo de execucao nao e medido aqui; depois do lote, rode remedir_v3.py.
"""
import sys
from pathlib import Path

from src.db import get_engine
from src.experimento import celula, introspec, persistencia
from src.llm.factory import escolher_modelo
from src.prompts.contexto import Nivel


def carregar_consultas(pasta, somente=None):
    """Le os .sql da pasta (sem as linhas de comentario) e devolve [(nome, sql)]."""
    consultas = []
    for arquivo in sorted(Path(pasta).glob("*.sql")):
        if somente and arquivo.stem not in somente:
            continue
        linhas = [l for l in arquivo.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--")]
        consultas.append((arquivo.stem, "\n".join(linhas).strip().rstrip(";")))
    return consultas


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    run_id = args[0]
    pasta = args[1] if len(args) > 1 else "benchmarks/controlled/queries"
    benchmark = args[2] if len(args) > 2 else "controlled"
    somente = set(args[3].split(",")) if len(args) > 3 and args[3] != "-" else None
    fases = [Nivel(x) for x in args[4].split(",")] if len(args) > 4 else list(Nivel)

    modelo = escolher_modelo()
    engine = get_engine()
    persistencia.criar_tabela(engine)
    consultas = carregar_consultas(pasta, somente)
    total = len(consultas) * len(fases)
    print(f"run_id={run_id} modelo={modelo.model} benchmark={benchmark} banco={engine.url.database} "
          f"consultas={len(consultas)} fases={','.join(f.value for f in fases)} esquema={introspec.formato_padrao()}", flush=True)

    n = 0
    for query_id, sql in consultas:
        for fase in fases:
            n += 1
            linha = celula.executar_celula(engine, modelo, run_id, benchmark, query_id, sql, fase)
            persistencia.gravar(engine, linha)
            custo = ""
            if linha["custo_original"] and linha["custo_reescrita"]:
                custo = f"custo {linha['custo_original']:.0f} -> {linha['custo_reescrita']:.0f}"
            print(f"[{n:>3}/{total}] {query_id:<16} {fase.value} {linha['decisao']:<22} {custo}", flush=True)
    print("lote concluido", flush=True)


if __name__ == "__main__":
    main()
