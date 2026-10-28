-- id: subconsulta_02
-- categoria: subconsulta/CTE
-- defeito: subconsulta correlacionada com count(*) usada apenas para testar existencia.
-- reescrita esperada: EXISTS (ou juncao semi) equivalente.
SELECT c.id, c.nome
FROM cliente c
WHERE (SELECT count(*) FROM pedido p WHERE p.cliente_id = c.id AND p.status = 'cancelado') >= 1;
