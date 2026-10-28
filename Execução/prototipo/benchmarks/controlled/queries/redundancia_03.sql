-- id: redundancia_03
-- categoria: redundancia
-- defeito: COUNT(DISTINCT id) sobre a chave primaria (id ja e unico).
-- reescrita esperada: COUNT(*).
SELECT count(DISTINCT id) AS n FROM pedido;
