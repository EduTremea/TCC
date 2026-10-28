-- Base controlada (dominio proprio: loja/vendas).
-- Proposito duplo:
--   1. suporte ao conjunto de consultas deliberadamente ruins (uma por categoria);
--   2. base "off-repertoire" (fora do repertorio publico dos modelos), para mitigar
--      a memorizacao de pre-treino discutida na orientacao de 18/09.
-- Deve ser aplicada com seed.sql (dados reprodutiveis: random() com setseed(0.42)).

DROP TABLE IF EXISTS item_pedido, pedido, produto, cliente CASCADE;

CREATE TABLE cliente (
    id         integer PRIMARY KEY,
    nome       text    NOT NULL,
    cidade     text    NOT NULL,
    uf         char(2) NOT NULL,
    criado_em  date    NOT NULL
);

CREATE TABLE produto (
    id        integer      PRIMARY KEY,
    nome      text         NOT NULL,
    categoria text         NOT NULL,
    preco     numeric(10,2) NOT NULL
);

CREATE TABLE pedido (
    id         integer PRIMARY KEY,
    cliente_id integer NOT NULL REFERENCES cliente(id),
    data       date    NOT NULL,
    status     text    NOT NULL,
    cupom_id   integer            -- anulavel de proposito (armadilha NOT IN / NULL)
);

CREATE TABLE item_pedido (
    id         integer       PRIMARY KEY,
    pedido_id  integer       NOT NULL REFERENCES pedido(id),
    produto_id integer       NOT NULL REFERENCES produto(id),
    quantidade integer       NOT NULL,
    preco_unit numeric(10,2) NOT NULL
);

-- Indices: habilitam ganhos reais em reescritas sargaveis e em juncoes.
CREATE INDEX idx_pedido_cliente ON pedido(cliente_id);
CREATE INDEX idx_pedido_data    ON pedido(data);
CREATE INDEX idx_item_pedido    ON item_pedido(pedido_id);
CREATE INDEX idx_item_produto   ON item_pedido(produto_id);
