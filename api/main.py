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
