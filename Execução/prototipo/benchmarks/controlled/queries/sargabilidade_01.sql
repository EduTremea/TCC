-- id: sargabilidade_01
-- categoria: sargabilidade
-- defeito: EXTRACT(YEAR FROM data) aplica funcao sobre a coluna filtrada e
--   impede o uso do indice idx_pedido_data (forca seq scan).
-- reescrita esperada: predicado de faixa sargavel, preservando o resultado:
--   data >= DATE '2023-01-01' AND data < DATE '2024-01-01'
SELECT status, count(*) AS total
FROM pedido
WHERE EXTRACT(YEAR FROM data) = 2023
GROUP BY status;
