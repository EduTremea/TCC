# TPC-H (fator de escala 1)

Base de referência da literatura, carregada em um banco separado (`tpch`) no mesmo contêiner. O experimento usa as consultas Q03, Q04, Q06 e Q18.

## Geração e carga

Os dados e as 22 consultas oficiais vêm do gerador do TPC-H embutido no DuckDB, o que evita compilar o `dbgen` no Windows.

```bash
# 1. gerar data/tpch/*.csv e benchmarks/tpch/queries/qNN.sql
uv run --with duckdb python gen_tpch.py

# 2. criar o banco e as tabelas
docker exec tcc_postgres psql -U postgres -d tcc -c "CREATE DATABASE tpch;"
docker exec -i tcc_postgres psql -U postgres -d tpch -f - < benchmarks/tpch/schema.sql

# 3. carregar cada tabela (region, nation, part, supplier, partsupp, customer, orders, lineitem)
docker exec -i tcc_postgres psql -U postgres -d tpch -c "\copy lineitem FROM STDIN WITH (FORMAT csv, HEADER true)" < data/tpch/lineitem.csv

# 4. chaves, índices e ANALYZE
docker exec -i tcc_postgres psql -U postgres -d tpch -f - < benchmarks/tpch/constraints.sql
```

| Tabela | Linhas |
|---|---|
| region | 5 |
| nation | 25 |
| supplier | 10.000 |
| customer | 150.000 |
| part | 200.000 |
| partsupp | 800.000 |
| orders | 1.500.000 |
| lineitem | 6.001.215 |

Os CSV em `data/tpch/` são gerados localmente e não entram no repositório.

## Rodar a matriz sobre o TPC-H

```bash
POSTGRES_DB=tpch OLLAMA_MODEL=llama3 uv run python rodar_lote.py tpch-llama3 benchmarks/tpch/queries tpch q03,q04,q06,q18
```
