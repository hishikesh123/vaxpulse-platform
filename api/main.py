from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.db import get_conn

app = FastAPI(title="VaxPulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/countries")
def get_countries():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT country_name
                    FROM Location
                    WHERE country_name IS NOT NULL
                    ORDER BY country_name;
                """)
                return [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/kpi/monthly-growth/{country}")
def monthly_growth(country: str):
    """
    Month-end total vaccinations and MoM growth rate.
    IMPORTANT: use month-end (not SUM) for cumulative totals.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH daily AS (
                      SELECT
                        date::date AS d,
                        total_vaccination::bigint AS total
                      FROM Vaccination
                      WHERE location = %s AND total_vaccination IS NOT NULL
                    ),
                    month_end AS (
                      SELECT
                        date_trunc('month', d)::date AS month,
                        MAX(total) AS total
                      FROM daily
                      GROUP BY 1
                    ),
                    growth AS (
                      SELECT
                        month,
                        total,
                        CASE
                          WHEN LAG(total) OVER (ORDER BY month) IS NULL THEN NULL
                          WHEN LAG(total) OVER (ORDER BY month) = 0 THEN NULL
                          ELSE (total - LAG(total) OVER (ORDER BY month))::float
                               / LAG(total) OVER (ORDER BY month)
                        END AS growth_rate
                      FROM month_end
                    )
                    SELECT month, total, growth_rate
                    FROM growth
                    ORDER BY month;
                """, (country,))
                rows = cur.fetchall()

        return [
            {"month": r[0].isoformat(), "total": int(r[1]), "growth_rate": (float(r[2]) if r[2] is not None else None)}
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"monthly_growth failed: {e}")


@app.get("/kpi/manufacturer-share/{country}")
def manufacturer_share(country: str):
    """
    Manufacturer totals on the latest available date for the selected country.
    Avoid summing cumulative totals across dates.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # find latest date for that country
                cur.execute("""
                    SELECT MAX(date::date)
                    FROM Vaccination_by_manu
                    WHERE country_name = %s;
                """, (country,))
                latest = cur.fetchone()[0]
                if latest is None:
                    return []

                cur.execute("""
                    SELECT vaccine, total_vaccinations::bigint AS total
                    FROM Vaccination_by_manu
                    WHERE country_name = %s AND date::date = %s
                      AND total_vaccinations IS NOT NULL
                    ORDER BY total DESC
                    LIMIT 15;
                """, (country, latest))
                rows = cur.fetchall()

        return [{"vaccine": r[0], "total": int(r[1])} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"manufacturer_share failed: {e}")
