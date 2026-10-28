-- id: subconsulta_03
-- categoria: subconsulta/CTE
-- defeito: filtro via IN (subconsulta) que poderia ser uma juncao.
-- reescrita esperada: JOIN com produto (categoria = 'Bebidas').
SELECT DISTINCT i.pedido_id
FROM item_pedido i
WHERE i.produto_id IN (SELECT pr.id FROM produto pr WHERE pr.categoria = 'Bebidas');
