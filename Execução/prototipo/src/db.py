"""Conexao com o PostgreSQL. Os parametros vem do .env ou dos padroes abaixo."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def get_engine():
    user = os.getenv("POSTGRES_USER", "postgres")
    senha = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    porta = os.getenv("POSTGRES_PORT", "5432")
    banco = os.getenv("POSTGRES_DB", "tcc")
    url = f"postgresql+psycopg://{user}:{senha}@{host}:{porta}/{banco}"
    # statement_timeout: nenhuma consulta roda mais de 5 minutos. Se estourar, a
    # execucao e registrada como erro e o lote continua.
    return create_engine(url, pool_pre_ping=True, connect_args={"options": "-c statement_timeout=300000"})


if __name__ == "__main__":
    with get_engine().connect() as conn:
        print(conn.execute(text("SELECT version()")).scalar_one())
