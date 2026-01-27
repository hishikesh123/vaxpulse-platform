import os
from pathlib import Path
import psycopg

def run_sql_file(conn, path: Path):
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)

def main():
    dsn = os.environ.get("PG_DSN")
    if not dsn:
        raise RuntimeError("PG_DSN env var not set. Add it in Render Environment settings.")

    migrations_dir = Path("sql/migrations")
    files = sorted(migrations_dir.glob("*.sql"))

    if not files:
        raise RuntimeError("No migration files found in sql/migrations/")

    with psycopg.connect(dsn) as conn:
        # Ensure idempotent / safe re-runs by using IF NOT EXISTS in SQL
        for f in files:
            print(f"Applying migration: {f}")
            run_sql_file(conn, f)
        conn.commit()

    print("✅ Migrations applied successfully.")

if __name__ == "__main__":
    main()
