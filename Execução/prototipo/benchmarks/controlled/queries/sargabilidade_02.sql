-- id: sargabilidade_02
-- categoria: sargabilidade
-- defeito: aritmetica sobre a coluna 'data' (data - DATE ...) impede o indice idx_pedido_data.
-- reescrita esperada: data > DATE '2022-01-01' + 400 (sargavel), preservando o resultado.
SELECT status, count(*) AS total
FROM pedido
WHERE data - DATE '2022-01-01' > 400
GROUP BY status;
