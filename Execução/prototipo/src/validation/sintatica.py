"""V1: a reescrita compila? O EXPLAIN faz o PostgreSQL analisar e planejar sem executar."""
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError


def valida_sintaxe(engine, sql):
    """Devolve (ok, mensagem_de_erro)."""
    try:
        with engine.connect() as conn:
            conn.execute(text(f"EXPLAIN {sql}"))
        return True, None
    except DatabaseError as exc:
        return False, str(exc.orig)
