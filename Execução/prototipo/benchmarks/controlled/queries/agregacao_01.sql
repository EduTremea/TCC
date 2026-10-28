-- id: agregacao_01
-- categoria: agregacao
-- defeito: total por pedido calculado com subconsulta escalar correlacionada,
--   reexecutando a agregacao para cada linha de pedido.
-- reescrita esperada: uma unica agregacao com LEFT JOIN e GROUP BY. Nesta base ha
--   pedidos sem itens (item_pedido.pedido_id e sorteado no seed.sql); uma juncao
--   interna os descarta e o validador rejeita a reescrita por resultado.
SELECT p.id,
       (SELECT sum(i.quantidade * i.preco_unit)
          FROM item_pedido i
         WHERE i.pedido_id = p.id) AS total
FROM pedido p
WHERE p.status = 'pago';
