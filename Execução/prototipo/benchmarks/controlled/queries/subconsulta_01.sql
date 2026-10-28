-- id: subconsulta_01
-- categoria: subconsulta/CTE
-- defeito: subconsulta correlacionada reexecutada uma vez por cliente.
-- reescrita esperada: juncao + GROUP BY/HAVING equivalente, por exemplo
--   SELECT c.id, c.nome FROM cliente c JOIN pedido p ON p.cliente_id = c.id
--   GROUP BY c.id, c.nome HAVING count(*) > 12
SELECT c.id, c.nome
FROM cliente c
WHERE (SELECT count(*) FROM pedido p WHERE p.cliente_id = c.id) > 12;
