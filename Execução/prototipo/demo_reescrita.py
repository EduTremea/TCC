"""Uma execucao completa, visivel: subconsulta_01 na fase C1 com o modelo configurado.

Uso:
    uv run python demo_reescrita.py            (precisa do banco tcc carregado e do Ollama rodando)

Mostra o prompt, a reescrita devolvida, o que cada verificacao decidiu e, se a
reescrita passou, o custo estimado e a razao de tempo. Nada e gravado no banco.
"""
from src.db import get_engine
from src.experimento.celula import executar_celula
from src.llm.factory import escolher_modelo
from src.prompts.contexto import Nivel
from src.validation.desempenho import LIMIAR_TEMPO, medir_intercalado
from rodar_lote import carregar_consultas


def main():
    engine = get_engine()
    modelo = escolher_modelo()
    (query_id, sql), = carregar_consultas("benchmarks/controlled/queries", {"subconsulta_01"})
    linha = executar_celula(engine, modelo, "demo", "controlled", query_id, sql, Nivel.C1)

    print("=== prompt enviado ===")
    print(linha["prompt"])
    print("\n=== reescrita devolvida ===")
    print(linha["sql_reescrita"])
    print(f"\nsintaxe ok: {linha['v1_ok']}   mesmo resultado: {linha['v2_ok']}   decisao: {linha['decisao']}")
    if linha["erro"]:
        print("erro:", linha["erro"])
    if linha["decisao"] != "pendente_medicao":
        return

    print(f"custo estimado: {linha['custo_original']:.0f} -> {linha['custo_reescrita']:.0f}")
    medida = medir_intercalado(engine, sql, linha["sql_reescrita"])
    print(f"tempo (mediana de 5 pares): {medida['tempo_original_ms']:.1f} ms -> {medida['tempo_reescrita_ms']:.1f} ms; "
          f"razao {medida['razao_mediana']:.2f} (limiar {LIMIAR_TEMPO})")
    if linha["custo_reescrita"] < linha["custo_original"]:
        print("categoria: otimizada")
    else:
        print("categoria: valida sem ganho")


if __name__ == "__main__":
    main()
