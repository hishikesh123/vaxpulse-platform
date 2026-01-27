import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    dsn = os.environ["PG_DSN"]
    return psycopg.connect(dsn)
