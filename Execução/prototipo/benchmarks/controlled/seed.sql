-- Dados reprodutiveis com variancia natural.
-- Reprodutibilidade: setseed(0.42) fixa o gerador para a sessao; executar este
-- arquivo inteiro em uma unica sessao psql reproduz exatamente a mesma carga.
-- Evita os artefatos de alinhamento por modulo (ex.: todo cliente com o mesmo
-- numero de pedidos ou o mesmo status).

SELECT setseed(0.42);

INSERT INTO cliente (id, nome, cidade, uf, criado_em)
SELECT g,
       'Cliente ' || g,
       (ARRAY['Passo Fundo','Porto Alegre','Carazinho','Erechim','Marau'])[1 + floor(random() * 5)::int],
       (ARRAY['RS','SC','PR','SP','MG'])[1 + floor(random() * 5)::int],
       DATE '2020-01-01' + floor(random() * 1000)::int
FROM generate_series(1, 5000) AS g;

INSERT INTO produto (id, nome, categoria, preco)
SELECT g,
       'Produto ' || g,
       (ARRAY['Bebidas','Limpeza','Higiene','Alimentos','Eletronicos',
              'Papelaria','Pet','Ferramentas','Vestuario','Brinquedos'])[1 + floor(random() * 10)::int],
       (10 + floor(random() * 100))::numeric(10,2)
FROM generate_series(1, 500) AS g;

-- cliente_id aleatorio -> numero de pedidos por cliente varia (Poisson ~10),
-- tornando HAVING/count significativos. status e cupom variam dentro do cliente.
INSERT INTO pedido (id, cliente_id, data, status, cupom_id)
SELECT g,
       1 + floor(random() * 5000)::int,
       DATE '2022-01-01' + floor(random() * 1000)::int,
       (ARRAY['pago','pago','pago','pendente','cancelado'])[1 + floor(random() * 5)::int],
       CASE WHEN random() < 0.33 THEN NULL ELSE floor(random() * 100)::int END
FROM generate_series(1, 50000) AS g;

-- pedido_id aleatorio -> alguns pedidos ficam sem itens, o que torna a
-- verificacao de equivalencia da agregacao real (INNER JOIN ingenuo derruba
-- esses pedidos; so LEFT JOIN preserva o resultado).
INSERT INTO item_pedido (id, pedido_id, produto_id, quantidade, preco_unit)
SELECT g,
       1 + floor(random() * 50000)::int,
       1 + floor(random() * 500)::int,
       1 + floor(random() * 5)::int,
       (10 + floor(random() * 100))::numeric(10,2)
FROM generate_series(1, 150000) AS g;

ANALYZE;
