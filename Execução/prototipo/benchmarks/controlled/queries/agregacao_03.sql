-- id: agregacao_03
-- categoria: agregacao
-- defeito: contagem de distintos feita com subconsulta em FROM + GROUP BY.
-- reescrita esperada: SELECT count(DISTINCT cliente_id) FROM pedido.
SELECT count(*) AS n
FROM (SELECT cliente_id FROM pedido GROUP BY cliente_id) t;
