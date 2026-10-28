-- id: juncao_03
-- categoria: logica de juncao
-- defeito: juncao implicita de 3 tabelas no WHERE (estilo cross join filtrado).
-- reescrita esperada: JOINs explicitos equivalentes.
SELECT ip.id
FROM item_pedido ip, pedido p, cliente c
WHERE ip.pedido_id = p.id
  AND p.cliente_id = c.id
  AND c.uf = 'SC';
