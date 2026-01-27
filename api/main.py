from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="VaxPulse API")

# Safe default CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
from api.db import get_conn

@app.get("/debug/location_count")
def debug_location_count():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM location;")
        n = cur.fetchone()[0]
        cur.execute("SELECT country_name FROM location ORDER BY country_name;")
        names = [r[0] for r in cur.fetchall()]
    return {"location_count": n, "countries": names}


@app.get("/countries")
def get_countries():
    return ["Australia", "India", "USA"]

@app.get("/kpi/monthly-growth/{country}")
def monthly_growth(country: str):
    return [
        {"month": "2023-01-01", "total": 100, "growth_rate": 0.10},
        {"month": "2023-02-01", "total": 120, "growth_rate": 0.20},
    ]

@app.get("/kpi/manufacturer-share/{country}")
def manufacturer_share(country: str):
    return [
        {"vaccine": "Pfizer", "total": 500},
        {"vaccine": "Moderna", "total": 300},
    ]
