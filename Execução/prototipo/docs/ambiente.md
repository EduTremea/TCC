# Ambiente de medição — configuração fixada

> Esta configuração é a **linha de base**. Qualquer alteração aqui invalida as
> medições já coletadas e exige refazer a linha de base.

## SGBD

- **PostgreSQL 14.24** em Docker (imagem `postgres:14`), container `tcc_postgres`.
- Escolha da versão 14: paridade com R-Bot e QUITE (ambos PostgreSQL 14.x).

## Parâmetros fixados (via `docker-compose.yml`)

| Parâmetro | Valor | Motivo |
|---|---|---|
| `shared_preload_libraries` | `pg_stat_statements` | conferência de tempos por consulta |
| `shared_buffers` | 512 MB | cache de buffers estável entre execuções |
| `work_mem` | 64 MB | memória de ordenação/hash previsível |
| `effective_cache_size` | 2 GB | estimativa de cache para o planejador |
| `track_io_timing` | on | tempos de I/O no `EXPLAIN (ANALYZE, BUFFERS)` |

Valores confirmados via `pg_settings` em 2026-09-29.

## Máquina de desenvolvimento

- 16 GB RAM, CPU 12 núcleos, **sem GPU dedicada** (Intel UHD). Inferência de LLM
  local em CPU — modelos pequenos (3B–8B) via Ollama.

## Como recriar do zero

```bash
cd prototipo
docker compose down -v          # apaga o volume (perde os dados)
docker compose up -d
docker exec tcc_postgres psql -U postgres -d tcc -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
docker exec -i tcc_postgres psql -U postgres -d tcc -v ON_ERROR_STOP=1 < benchmarks/controlled/schema.sql
docker exec -i tcc_postgres psql -U postgres -d tcc -v ON_ERROR_STOP=1 < benchmarks/controlled/seed.sql
```

A carga é reprodutível: `seed.sql` fixa `setseed(0.42)` antes dos inserts.
