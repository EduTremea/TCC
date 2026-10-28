-- id: correcao_01
-- categoria: correcao (armadilha de equivalencia)
-- defeito/armadilha: NOT IN sobre uma subconsulta que PODE conter NULL (cupom_id
--   e anulavel). A reescrita "obvia" para NOT EXISTS / anti-juncao NAO e
--   equivalente quando ha NULL: NOT IN com algum NULL na lista retorna vazio,
--   enquanto o anti-join retornaria linhas.
-- proposito: este caso NAO busca ganho de desempenho. Ele testa o VALIDADOR:
--   uma reescrita ingenua (NOT EXISTS) deve ser REJEITADA na verificacao semantica (V2).
SELECT c.id, c.nome
FROM cliente c
WHERE c.id NOT IN (SELECT pe.cupom_id FROM pedido pe WHERE pe.status = 'pago');
