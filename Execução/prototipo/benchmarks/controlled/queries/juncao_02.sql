-- id: juncao_02
-- categoria: logica de juncao
-- defeito: juncao com cliente sem usar nenhuma coluna dele; a FK garante
--   correspondencia unica, entao a juncao e desnecessaria.
-- reescrita esperada: remover a juncao -> SELECT id FROM pedido WHERE status = 'pago'.
SELECT p.id
FROM pedido p
JOIN cliente c ON c.id = p.cliente_id
WHERE p.status = 'pago';
