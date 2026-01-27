from fastapi import FastAPI
from api.db import get_conn

app = FastAPI(title="VaxPulse API")

@app.get("/countries")
def countries():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT country_name FROM location ORDER BY country_name;")
        return [r[0] for r in cur.fetchall()]

@app.get("/kpi/monthly-growth/{country_name}")
def monthly_growth(country_name: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT month, month_end_total_vaccinations, growth_rate
            FROM vw_country_monthly_growth
            WHERE country_name = %s
            ORDER BY month;
            """,
            (country_name,),
        )
        rows = cur.fetchall()
        return [{"month": r[0].isoformat(), "total": r[1], "growth_rate": r[2]} for r in rows]

@app.get("/kpi/manufacturer-share/{country_name}")
def manufacturer_share(country_name: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT vaccine,
                   SUM(total_vaccinations) AS total
            FROM vaccination_by_manu
            WHERE country_name = %s
            GROUP BY vaccine
            ORDER BY total DESC
            LIMIT 15;
            """,
            (country_name,),
        )
        rows = cur.fetchall()
        return [{"vaccine": r[0], "total": r[1]} for r in rows]
