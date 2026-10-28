# Protótipo: reescrita de consultas SQL por modelos de linguagem, validada pelo PostgreSQL

O modelo recebe a consulta (e, conforme a fase, esquema, estatísticas e plano) e devolve uma reescrita. O banco verifica se ela compila, se devolve as mesmas linhas, se é diferente da original e se tem custo estimado menor. O tempo é medido depois, em lote, com nenhum modelo carregado.

## Reprodução

Os comandos abaixo estão em sintaxe Bash e devem ser executados nesta pasta. No Windows, use o Git Bash: o PowerShell não aceita o redirecionamento com `<` nem a forma `VARIAVEL=valor comando`.

1. Requisitos: Docker Desktop, [uv](https://docs.astral.sh/uv/) (que instala o Python 3.12 exigido) e [Ollama](https://ollama.com/) com `ollama pull llama3.2` (3B) e `ollama pull llama3` (8B).
2. `cp .env.example .env`. Para o modelo pago, preencha `OPENAI_API_KEY` só no `.env`, que não é versionado.
3. `uv sync` e `docker compose up -d` (PostgreSQL 14 com os parâmetros de `docs/ambiente.md`).
4. Base controlada: `docker exec -i tcc_postgres psql -U postgres -d tcc -f - < benchmarks/controlled/schema.sql`, depois o mesmo com `seed.sql`.
5. TPC-H (opcional, 1 GB): `uv run --with duckdb python gen_tpch.py` gera os CSV e as consultas; a carga no banco `tpch` segue `benchmarks/tpch/README.md`.
6. Uma execução visível, sem gravar nada: `uv run python demo_reescrita.py`.
7. Um lote: `OLLAMA_MODEL=llama3 uv run python rodar_lote.py <run_id>` (para o pago, `LLM_PROVIDER=openai`; para o TPC-H, `POSTGRES_DB=tpch` e a pasta `benchmarks/tpch/queries`). O lote grava sintaxe, resultado e custo; o tempo fica para o passo seguinte.
8. Tempo, com nenhum modelo carregado: `uv run python remedir_v3.py remedir tcc - <run_id>` cria a rodada `v3-<run_id>`. `uv run python remedir_v3.py aa` mede cada consulta contra ela mesma, para calibrar o limiar.
9. Tabelas, CSV e figuras: `uv run python analise_v4.py` (saída em `results/final_v4/`). Tipos de erro das reescritas inválidas e tempo de inferência: `uv run python complementos.py`. Planilha: `uv run --with openpyxl python gerar_planilha.py`. O `analise_v4.py` e o `complementos.py` leem o banco, cujos dados não são versionados, e a planilha parte dos CSV gerados por eles; a saída usada no artigo está em [`../resultados/`](../resultados/), com todas as execuções classificadas, e para atualizá-la basta copiar para lá o conteúdo de `results/final_v4/`.
10. Testes: `uv run pytest`.

## Pastas

- `src/llm/` clientes do Ollama e da API do modelo pago, uma chamada independente por execução.
- `src/prompts/` montagem do prompt das fases C0 a C3 e o catálogo de transformações.
- `src/validation/` sintaxe (EXPLAIN), resultado (comparação das linhas), custo e tempo (medição intercalada).
- `src/experimento/` contexto extraído do banco, execução de uma célula e gravação na tabela `resultado`.
- `benchmarks/` esquema, dados e consultas da base controlada; esquema e consultas do TPC-H.
- `tests/` testes dos prompts, do formatador de esquema e da comparação de resultados, sem banco.
