-- id: redundancia_02
-- categoria: redundancia
-- defeito: UNION de dois filtros mutuamente exclusivos sobre a mesma tabela.
-- reescrita esperada: WHERE uf IN ('RS','SC') (os ids sao unicos, entao equivalente).
SELECT id, nome FROM cliente WHERE uf = 'RS'
UNION
SELECT id, nome FROM cliente WHERE uf = 'SC';
