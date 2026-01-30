import os
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

# -------------------------
# Health
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# Countries
# -------------------------
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch countries: {e}")


# -------------------------
# KPI: Monthly Growth (month-end totals + MoM growth)
# -------------------------
@app.get("/kpi/monthly-growth/{country}")
def monthly_growth(country: str):
    """
    Returns:
      [{"month": "YYYY-MM-01", "total": <month_end_total>, "growth_rate": <mom_ratio_or_null>}, ...]
    NOTE: For cumulative totals, we do NOT sum totals across month.
          We take month-end (MAX within month) as an approximation.
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
                      WHERE location = %s
                        AND total_vaccination IS NOT NULL
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
            {
                "month": r[0].isoformat(),
                "total": int(r[1]),
                "growth_rate": (float(r[2]) if r[2] is not None else None),
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"monthly_growth failed: {e}")


# -------------------------
# KPI: Manufacturer share (latest snapshot)
# -------------------------
@app.get("/kpi/manufacturer-share/{country}")
def manufacturer_share(country: str):
    """
    Returns top manufacturers for the LATEST date available for the country.
    Avoid summing cumulative totals across multiple dates.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # latest date for the country
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
                    WHERE country_name = %s
                      AND date::date = %s
                      AND total_vaccinations IS NOT NULL
                    ORDER BY total DESC
                    LIMIT 15;
                """, (country, latest))
                rows = cur.fetchall()

        return [{"vaccine": r[0], "total": int(r[1])} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"manufacturer_share failed: {e}")


# -------------------------
# Meta: last updated
# -------------------------
@app.get("/meta/last-updated/{country}")
def meta_last_updated_country(country: str):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MAX(date::date)
                    FROM Vaccination
                    WHERE location = %s;
                """, (country,))
                d = cur.fetchone()[0]
        return {"country": country, "last_updated": d.isoformat() if d else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"meta_last_updated_country failed: {e}")


# -------------------------
# Quality: summary
# -------------------------
@app.get("/quality/summary/{country}")
def quality_summary(country: str):
    """
    Lightweight quality summary:
      - months observed
      - missing months (based on min/max range)
      - null rate for total_vaccination
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Count observed distinct months
                cur.execute("""
                    SELECT COUNT(DISTINCT date_trunc('month', date::date))
                    FROM Vaccination
                    WHERE location = %s;
                """, (country,))
                observed_months = cur.fetchone()[0] or 0

                # Expected months from min->max
                cur.execute("""
                    WITH bounds AS (
                      SELECT
                        date_trunc('month', MIN(date::date)) AS min_m,
                        date_trunc('month', MAX(date::date)) AS max_m
                      FROM Vaccination
                      WHERE location = %s
                    ),
                    all_months AS (
                      SELECT generate_series(min_m, max_m, interval '1 month') AS m
                      FROM bounds
                      WHERE min_m IS NOT NULL AND max_m IS NOT NULL
                    )
                    SELECT COUNT(*) FROM all_months;
                """, (country,))
                expected_months = cur.fetchone()[0] or 0

                missing_months = max(expected_months - observed_months, 0)

                # Null rate for total_vaccination
                cur.execute("""
                    SELECT
                      CASE WHEN COUNT(*) = 0 THEN 0
                           ELSE SUM(CASE WHEN total_vaccination IS NULL THEN 1 ELSE 0 END)::float / COUNT(*)
                      END AS null_rate_total
                    FROM Vaccination
                    WHERE location = %s;
                """, (country,))
                null_rate_total = cur.fetchone()[0] or 0.0

        return {
            "country": country,
            "months": int(observed_months),
            "missing_months": int(missing_months),
            "null_rate_total": float(null_rate_total),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"quality_summary failed: {e}")
