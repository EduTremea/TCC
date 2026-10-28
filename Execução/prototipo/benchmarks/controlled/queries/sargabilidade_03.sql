-- id: sargabilidade_03
-- categoria: sargabilidade
-- defeito: aritmetica sobre produto_id (produto_id + 0) impede o indice idx_item_produto.
-- reescrita esperada: produto_id = 42.
SELECT count(*) AS itens
FROM item_pedido
WHERE produto_id + 0 = 42;
