"""Planilha com todas as execucoes do conjunto final, a partir dos CSVs gerados por analise_v4.py.

Uso:
    uv run --with openpyxl python gerar_planilha.py      (saida: results/final_v4/execucoes.xlsx)

Abas:
    execucoes  uma linha por execucao, com a categoria e o prompt completo
    resumo     contagem por banco, modelo, fase e repeticao em cada categoria (formulas COUNTIFS)
    legenda    o que significa cada coluna
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ENTRADA = {"tcc": "results/final_v4/tcc_execucoes_classificadas.csv", "tpch": "results/final_v4/tpch_execucoes_classificadas.csv"}
SAIDA = "results/final_v4/execucoes.xlsx"
CATEGORIAS = ["invalida_sintaxe", "invalida_resultado", "sem_mudanca", "valida_sem_ganho", "otimizada"]

COLUNAS = ["banco", "run_id", "repeticao", "query_id", "fase", "modelo", "categoria", "v1_ok", "v2_ok",
           "linhas_original", "linhas_reescrita", "custo_original", "custo_reescrita", "ganho_custo",
           "tempo_original_ms", "tempo_reescrita_ms", "razao_tempo", "tempo_llm_ms", "erro", "criado_em",
           "sql_original", "sql_reescrita", "prompt"]

LEGENDA = [
    ("banco", "tcc = base controlada (loja); tpch = TPC-H."),
    ("run_id", "Nome da rodada como gravado no banco; o sufixo -r2 ou -r3 e a repeticao."),
    ("repeticao", "1, 2 ou 3."),
    ("query_id", "Qual consulta (ex.: subconsulta_01; q06 = TPC-H Q6)."),
    ("fase", "C0 so a consulta; C1 + esquema e numero de linhas; C2 + catalogo de transformacoes; C3 + plano EXPLAIN."),
    ("modelo", "llama3.2 (3B, local), llama3 (8B, local) ou gpt-4o (pago, API)."),
    ("categoria", "invalida_sintaxe (nao executa), invalida_resultado (linhas diferentes), sem_mudanca (devolveu a original), "
                  "valida_sem_ganho (mesmo resultado, custo igual ou maior), otimizada (mesmo resultado, custo menor)."),
    ("v1_ok", "A reescrita compila (EXPLAIN)?"),
    ("v2_ok", "A reescrita devolve as mesmas linhas?"),
    ("linhas_original", "Linhas devolvidas pela consulta original."),
    ("linhas_reescrita", "Linhas devolvidas pela reescrita (vazio quando nao foi medida)."),
    ("custo_original", "Custo total do plano estimado pelo planejador para a original."),
    ("custo_reescrita", "Custo total do plano estimado para a reescrita."),
    ("ganho_custo", "custo_original / custo_reescrita."),
    ("tempo_original_ms", "Mediana de 5 medicoes da original (EXPLAIN ANALYZE), intercaladas com a reescrita."),
    ("tempo_reescrita_ms", "Mediana de 5 medicoes da reescrita."),
    ("razao_tempo", "Mediana das razoes tempo_original / tempo_reescrita dos 5 pares; mais rapida se >= 1,15."),
    ("tempo_llm_ms", "Tempo que o modelo levou para responder."),
    ("erro", "Mensagem de erro, quando houve."),
    ("criado_em", "Data e hora da execucao original."),
    ("sql_original", "A consulta enviada."),
    ("sql_reescrita", "A consulta devolvida pelo modelo."),
    ("prompt", "O texto completo enviado ao modelo."),
]


def carregar():
    partes = []
    for banco, caminho in ENTRADA.items():
        d = pd.read_csv(caminho)
        d.insert(0, "banco", banco)
        d = d.rename(columns={"rodada": "repeticao", "config": "fase", "categoria5": "categoria", "razao_mediana": "razao_tempo"})
        d["criado_em"] = pd.to_datetime(d["criado_em"], utc=True).dt.tz_localize(None)
        d["ganho_custo"] = d["ganho_custo"].round(3)
        partes.append(d[COLUNAS])
    return pd.concat(partes, ignore_index=True)


def main():
    df = carregar()
    wb = Workbook()
    negrito, normal = Font(name="Arial", bold=True), Font(name="Arial")
    cinza = PatternFill("solid", fgColor="E7E6E6")

    def cabecalho(ws):
        for c in ws[1]:
            c.font, c.fill = negrito, cinza
        ws.freeze_panes = "A2"

    ws = wb.active
    ws.title = "execucoes"
    ws.append(COLUNAS)
    for linha in df.itertuples(index=False):
        ws.append([None if (isinstance(v, float) and pd.isna(v)) or v is pd.NaT else v for v in linha])
    cabecalho(ws)
    ws.auto_filter.ref = ws.dimensions
    larguras = {"run_id": 26, "query_id": 18, "categoria": 20, "erro": 40, "criado_em": 19,
                "sql_original": 50, "sql_reescrita": 50, "prompt": 60}
    for i, nome in enumerate(COLUNAS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = larguras.get(nome, 13)

    # resumo: uma linha por banco x modelo x fase x repeticao, contagens por formula
    col = {nome: get_column_letter(i) for i, nome in enumerate(COLUNAS, start=1)}
    chaves = ["banco", "modelo", "fase", "repeticao"]
    grupos = df[chaves].drop_duplicates().sort_values(chaves)
    ws2 = wb.create_sheet("resumo")
    ws2.append(chaves + ["n"] + CATEGORIAS)
    r = 2
    for g in grupos.itertuples(index=False):
        criterios = ",".join(f"execucoes!${col[k]}:${col[k]},{get_column_letter(i + 1)}{r}" for i, k in enumerate(chaves))
        linha = [g.banco, g.modelo, g.fase, int(g.repeticao), f"=COUNTIFS({criterios})"]
        linha += [f'=COUNTIFS({criterios},execucoes!${col["categoria"]}:${col["categoria"]},"{c}")' for c in CATEGORIAS]
        ws2.append(linha)
        r += 1
    cabecalho(ws2)
    for i in range(1, len(chaves) + 1 + len(CATEGORIAS) + 1):
        ws2.column_dimensions[get_column_letter(i)].width = 18
    ws2.cell(row=r + 1, column=1, value="Cada numero e uma formula COUNTIFS sobre a aba execucoes; "
                                          "filtre aquela aba com os mesmos criterios para ver as linhas.").font = normal

    ws3 = wb.create_sheet("legenda")
    ws3.append(["coluna", "o que significa"])
    for nome, texto in LEGENDA:
        ws3.append([nome, texto])
    cabecalho(ws3)
    for linha in ws3.iter_rows(min_row=2):
        for c in linha:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws3.column_dimensions["A"].width = 20
    ws3.column_dimensions["B"].width = 110

    for folha in (ws, ws2, ws3):
        for linha in folha.iter_rows(min_row=2):
            for c in linha:
                c.font = normal

    wb.save(SAIDA)
    print(f"{SAIDA}: {len(df)} execucoes, {len(grupos)} linhas de resumo")


if __name__ == "__main__":
    main()
