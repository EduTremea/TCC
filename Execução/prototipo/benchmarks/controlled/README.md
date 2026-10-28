# Base controlada: consultas deliberadamente ineficientes

Esquema próprio de uma loja (cliente, produto, pedido, item_pedido) com 18 consultas, três por categoria de defeito. Serve como conjunto de defeitos conhecidos e como base que os modelos não viram no treinamento.

## Arquivos

- `schema.sql`: as quatro tabelas e os índices.
- `seed.sql`: dados reprodutíveis (`setseed(0.42)` antes dos inserts): 5.000 clientes, 500 produtos, 50.000 pedidos, 150.000 itens.
- `queries/`: as 18 consultas; cada arquivo traz em comentário o defeito e a reescrita esperada.

## Consultas

| Arquivo | Defeito | Reescrita esperada |
|---|---|---|
| `sargabilidade_01` | `EXTRACT` sobre a coluna impede o índice | faixa `data >= ... AND data < ...` |
| `sargabilidade_02` | aritmética sobre `data` impede o índice | faixa sargável |
| `sargabilidade_03` | `produto_id + 0` impede o índice | `produto_id = 42` |
| `subconsulta_01` | subconsulta correlacionada por linha | junção + `GROUP BY/HAVING` |
| `subconsulta_02` | subconsulta correlacionada só para testar existência | `EXISTS` |
| `subconsulta_03` | `IN (subconsulta)` | `JOIN` com produto |
| `juncao_01` | junção implícita no `WHERE` | `JOIN` explícito (mesmo plano) |
| `juncao_02` | junção com cliente sem usar colunas dele | remover a junção |
| `juncao_03` | junção implícita de três tabelas | `JOIN`s explícitos |
| `redundancia_01` | `DISTINCT` sobre chave + subconsulta sempre verdadeira | `SELECT` direto |
| `redundancia_02` | `UNION` de filtros exclusivos | `uf IN (...)` |
| `redundancia_03` | `COUNT(DISTINCT id)` sobre chave primária | `COUNT(*)` |
| `agregacao_01` | agregação escalar correlacionada por pedido | junção + `GROUP BY` |
| `agregacao_02` | agregação escalar por produto | `LEFT JOIN` + `GROUP BY` |
| `agregacao_03` | distintos via subconsulta em `FROM` | `COUNT(DISTINCT ...)` |
| `correcao_01` | `NOT IN` sobre coluna com `NULL` | nenhuma: `NOT EXISTS` muda o resultado |
| `correcao_02` | `DISTINCT` necessário após junção | nenhuma: removê-lo muda o resultado |
| `correcao_03` | `count(cupom_id)` ignora `NULL` | nenhuma: `count(*)` muda o resultado |

As três consultas de correção não buscam ganho. Elas existem para exercitar a verificação de resultado: a reescrita óbvia devolve linhas diferentes e deve ser rejeitada. `correcao_01` devolve zero linhas de propósito.
