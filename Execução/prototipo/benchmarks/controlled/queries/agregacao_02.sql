-- id: agregacao_02
-- categoria: agregacao
-- defeito: total de itens por produto via subconsulta escalar correlacionada.
-- reescrita esperada: LEFT JOIN item_pedido + GROUP BY (LEFT preserva produtos sem itens).
SELECT pr.id,
       (SELECT sum(i.quantidade) FROM item_pedido i WHERE i.produto_id = pr.id) AS itens
FROM produto pr;
