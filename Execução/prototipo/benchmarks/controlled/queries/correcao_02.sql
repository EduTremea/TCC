-- id: correcao_02
-- categoria: correcao (armadilha de equivalencia)
-- armadilha: o DISTINCT E necessario aqui, porque a juncao multiplica as ufs
--   (um cliente tem varios pedidos). Uma reescrita que REMOVA o DISTINCT muda o
--   resultado e deve ser REJEITADA pelo validador (V2).
SELECT DISTINCT c.uf
FROM cliente c
JOIN pedido p ON p.cliente_id = c.id
WHERE p.status = 'pago';
