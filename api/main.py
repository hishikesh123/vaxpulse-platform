import os
import csv
import io
from datetime import date
from typing import Optional
import pandas as pd
import requests
from fastapi import FastAPI, HTTPException, Query
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
# External data (optional fallback)
# -------------------------
OWID_VAX_CSV_URL = os.getenv(
    "OWID_VAX_CSV_URL",
    "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv",
)
USE_EXTERNAL_FALLBACK = os.getenv("USE_EXTERNAL_FALLBACK", "true").lower() in ("1", "true", "yes")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "25"))

# Cache external CSV in-memory for a short time (simple approach)
_external_cache = {"ts": None, "rows": None}

def _fetch_owid_csv_rows():
    """
    Downloads OWID vaccinations.csv and returns list of dict rows.
    Lightweight in-memory cache.
    """
    import time
    now = time.time()
    if _external_cache["rows"] is not None and _external_cache["ts"] is not None:
        # 10 minutes cache
        if now - _external_cache["ts"] < 600:
            return _external_cache["rows"]

    r = requests.get(OWID_VAX_CSV_URL, timeout=HTTP_TIMEOUT)
    r.raise_for_status()

    f = io.StringIO(r.text)
    reader = csv.DictReader(f)
    rows = list(reader)

    _external_cache["ts"] = now
    _external_cache["rows"] = rows
    return rows


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
    """
    Prefer DB countries.
    If DB is empty and fallback enabled, return countries from OWID CSV.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT country_name
                    FROM Location
                    WHERE country_name IS NOT NULL
                    ORDER BY country_name;
                """)
                rows = [r[0] for r in cur.fetchall()]
        if rows:
            return rows
    except Exception as e:
        # DB failed; try external if enabled
        if not USE_EXTERNAL_FALLBACK:
            raise HTTPException(status_code=500, detail=f"Failed to fetch countries: {e}")

    if USE_EXTERNAL_FALLBACK:
        try:
            rows = _fetch_owid_csv_rows()
            countries = sorted({r["location"] for r in rows if r.get("location")})
            return countries
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB empty/failed and external fetch failed: {e}")

    return []


# -------------------------
# KPI: Monthly Growth (DB)
# -------------------------
@app.get("/kpi/monthly-growth/{country}")
def monthly_growth(country: str):
    """
    Month-end total vaccinations + MoM growth rate (DB-backed).
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

        if rows:
            return [
                {"month": r[0].isoformat(), "total": int(r[1]), "growth_rate": (float(r[2]) if r[2] is not None else None)}
                for r in rows
            ]

    except Exception as e:
        if not USE_EXTERNAL_FALLBACK:
            raise HTTPException(status_code=500, detail=f"monthly_growth failed: {e}")

    # Optional external fallback for monthly growth
    if USE_EXTERNAL_FALLBACK:
        try:
            rows = _fetch_owid_csv_rows()
            # Filter rows for country; use date + total_vaccinations field (OWID)
            crows = [r for r in rows if r.get("location") == country and r.get("date") and r.get("total_vaccinations")]
            if not crows:
                return []

            df = pd.DataFrame(crows)
            df["date"] = pd.to_datetime(df["date"])
            df["total"] = pd.to_numeric(df["total_vaccinations"], errors="coerce")
            df = df.dropna(subset=["date", "total"]).sort_values("date")
            df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

            month_end = df.groupby("month")["total"].max().reset_index()
            month_end["growth_rate"] = month_end["total"].pct_change()

            return [
                {"month": d["month"].date().isoformat(), "total": int(d["total"]), "growth_rate": (None if pd.isna(d["growth_rate"]) else float(d["growth_rate"]))}
                for _, d in month_end.iterrows()
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"External monthly growth failed: {e}")

    return []


# -------------------------
# KPI: Manufacturer share (DB only; OWID has separate CSV for manufacturers)
# -------------------------
@app.get("/kpi/manufacturer-share/{country}")
def manufacturer_share(country: str):
    """
    Returns top manufacturers for the LATEST date available for the country (DB-backed).
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
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
# KPI tiles summary for Superset-style top cards
# -------------------------
@app.get("/kpi/summary/{country}")
def kpi_summary(country: str):
    """
    Summary KPIs to populate top cards.
    Uses DB monthly growth; falls back to external if enabled.
    """
    series = monthly_growth(country)
    if not series:
        return {"country": country, "latest_total": None, "latest_growth_rate": None, "peak_growth_rate": None, "as_of": None}

    latest = series[-1]
    growth_rates = [r["growth_rate"] for r in series if r.get("growth_rate") is not None]
    peak = max(growth_rates) if growth_rates else None

    return {
        "country": country,
        "latest_total": latest.get("total"),
        "latest_growth_rate": latest.get("growth_rate"),
        "peak_growth_rate": peak,
        "as_of": latest.get("month"),
    }


# -------------------------
# Meta: last updated
# -------------------------
@app.get("/meta/last-updated/{country}")
def meta_last_updated_country(country: str):
    """
    DB last-updated for this country. If DB empty and fallback enabled, infer from OWID.
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MAX(date::date)
                    FROM Vaccination
                    WHERE location = %s;
                """, (country,))
                d = cur.fetchone()[0]
        if d:
            return {"country": country, "last_updated": d.isoformat()}
    except Exception as e:
        if not USE_EXTERNAL_FALLBACK:
            raise HTTPException(status_code=500, detail=f"meta_last_updated_country failed: {e}")

    if USE_EXTERNAL_FALLBACK:
        try:
            rows = _fetch_owid_csv_rows()
            crows = [r for r in rows if r.get("location") == country and r.get("date")]
            if not crows:
                return {"country": country, "last_updated": None}
            last = max(r["date"] for r in crows)
            return {"country": country, "last_updated": last}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"External last-updated failed: {e}")

    return {"country": country, "last_updated": None}


# -------------------------
# Quality: summary
# -------------------------
@app.get("/quality/summary/{country}")
def quality_summary(country: str):
    """
    DB quality summary. (External quality can be added later if needed.)
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(DISTINCT date_trunc('month', date::date))
                    FROM Vaccination
                    WHERE location = %s;
                """, (country,))
                observed_months = cur.fetchone()[0] or 0

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


# -------------------------
# World map data (country comparison)
# -------------------------
@app.get("/map/world")
def map_world(metric: str = Query(..., description="latest_total_vaccinations | latest_mom_growth_rate")):
    if not USE_EXTERNAL_FALLBACK:
        raise HTTPException(status_code=400, detail="Enable USE_EXTERNAL_FALLBACK=true for world map.")

    try:
        rows = _fetch_owid_csv_rows()
        if not rows:
            raise HTTPException(status_code=500, detail="OWID CSV returned 0 rows")

        df = pd.DataFrame(rows)

        required_base = {"iso_code", "location", "date"}
        missing = required_base - set(df.columns)
        if missing:
            raise HTTPException(status_code=500, detail=f"OWID CSV missing columns: {sorted(missing)}")

        # Filter to countries only
        df = df[df["iso_code"].notna() & df["location"].notna() & df["date"].notna()]
        df = df[~df["iso_code"].str.startswith("OWID", na=False)]

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        if metric == "latest_total_vaccinations":
            if "total_vaccinations" not in df.columns:
                raise HTTPException(status_code=500, detail="OWID CSV missing total_vaccinations column")

            df["total_vaccinations"] = pd.to_numeric(df["total_vaccinations"], errors="coerce")
            df = df.dropna(subset=["total_vaccinations"])

            idx = df.groupby("location")["date"].idxmax()
            latest = df.loc[idx, ["location", "iso_code", "total_vaccinations"]].copy()
            latest = latest.rename(columns={"location": "country", "total_vaccinations": "value"})
            return latest.to_dict(orient="records")

        elif metric == "latest_mom_growth_rate":
            if "total_vaccinations" not in df.columns:
                raise HTTPException(status_code=500, detail="OWID CSV missing total_vaccinations column")

            df["total_vaccinations"] = pd.to_numeric(df["total_vaccinations"], errors="coerce")
            df = df.dropna(subset=["total_vaccinations"])

            df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
            month_end = df.groupby(["location", "iso_code", "month"])["total_vaccinations"].max().reset_index()
            month_end = month_end.sort_values(["location", "month"])
            month_end["growth_rate"] = month_end.groupby("location")["total_vaccinations"].pct_change()
            month_end = month_end.dropna(subset=["growth_rate"])

            if month_end.empty:
                return []

            idx = month_end.groupby("location")["month"].idxmax()
            latest = month_end.loc[idx, ["location", "iso_code", "growth_rate"]].copy()
            latest = latest.rename(columns={"location": "country", "growth_rate": "value"})
            return latest.to_dict(orient="records")

        else:
            raise HTTPException(status_code=400, detail="Unknown metric")

    except HTTPException:
        raise
    except Exception as e:
        # This makes the Render logs + client error clearer
        raise HTTPException(status_code=500, detail=f"map_world crashed: {type(e).__name__}: {e}")
