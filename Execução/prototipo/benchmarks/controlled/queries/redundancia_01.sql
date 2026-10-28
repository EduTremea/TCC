-- id: redundancia_01
-- categoria: redundancia
-- defeito: DISTINCT desnecessario (id ja e chave primaria) e subconsulta
--   correlacionada que sempre e verdadeira (c.id sempre esta entre os ids da
--   mesma uf), portanto um no-op.
-- reescrita esperada: SELECT id, nome FROM cliente (sem DISTINCT e sem subconsulta).
SELECT DISTINCT c.id, c.nome
FROM cliente c
WHERE c.id IN (SELECT c2.id FROM cliente c2 WHERE c2.uf = c.uf);
