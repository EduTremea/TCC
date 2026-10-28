-- id: juncao_01
-- categoria: logica de juncao
-- defeito: juncao implicita no WHERE (estilo cross join filtrado), menos legivel
--   e que pode atrapalhar a analise do otimizador.
-- reescrita esperada: JOIN explicito equivalente.
-- observacao: o ganho pode ser pequeno ou nulo (o otimizador ja lida bem com isto);
--   um resultado "sem ganho" tambem e valido, conforme orientacao.
SELECT p.id, c.nome
FROM pedido p, cliente c
WHERE p.cliente_id = c.id
  AND c.uf = 'RS'
  AND p.status = 'cancelado';
