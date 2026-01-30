import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    dsn = os.getenv("DATABASE_URL") or os.getenv("PG_DSN")
    if not dsn:
        raise RuntimeError("Set DATABASE_URL (Render) or PG_DSN (local) in environment")
    return psycopg.connect(dsn)
