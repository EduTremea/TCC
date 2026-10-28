-- id: correcao_03
-- categoria: correcao (armadilha de equivalencia)
-- armadilha: count(cupom_id) ignora NULL. Trocar por count(*) muda o resultado,
--   porque cupom_id e anulavel. A reescrita ingenua deve ser REJEITADA (V2).
SELECT count(cupom_id) AS n
FROM pedido
WHERE status = 'pago';
