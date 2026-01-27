import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="VaxPulse — Dashboard", layout="wide")
st.title("VaxPulse — Vaccination Analytics Dashboard")

session = requests.Session()

def _get_json(path: str):
    url = f"{API}{path}"
    r = session.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

# ✅ Cache network calls so Streamlit doesn't spam your API
@st.cache_data(ttl=600)
def fetch_countries():
    return _get_json("/countries")

@st.cache_data(ttl=300)
def fetch_monthly_growth(country: str):
    return _get_json(f"/kpi/monthly-growth/{country}")

@st.cache_data(ttl=300)
def fetch_manufacturer_share(country: str):
    return _get_json(f"/kpi/manufacturer-share/{country}")

# ---------- UI ----------
with st.sidebar:
    st.caption("API status")
    st.code(API)

try:
    countries = fetch_countries()
except Exception as e:
    st.error(
        f"Cannot reach FastAPI at **{API}**.\n\n"
        f"Set `API_URL` in your deployment environment to your public API URL.\n\n"
        f"Error: `{e}`"
    )
    st.stop()

country = st.selectbox("Select a country", countries)

st.subheader("Monthly Growth")
try:
    mg = fetch_monthly_growth(country)
    df_mg = pd.DataFrame(mg)
except Exception as e:
    st.error(f"Failed to load monthly growth for {country}: {e}")
    st.stop()

if not df_mg.empty:
    df_mg["month"] = pd.to_datetime(df_mg["month"])
    st.plotly_chart(
        px.line(df_mg, x="month", y="total", title="Total vaccinations (month-end)"),
        use_container_width=True,
    )
    st.plotly_chart(
        px.line(df_mg, x="month", y="growth_rate", title="Growth rate (MoM)"),
        use_container_width=True,
    )
else:
    st.info("No data for this country.")

st.subheader("Top Manufacturers (Total doses)")
try:
    ms = fetch_manufacturer_share(country)
    df_ms = pd.DataFrame(ms)
except Exception as e:
    st.error(f"Failed to load manufacturer share for {country}: {e}")
    st.stop()

if not df_ms.empty:
    st.plotly_chart(
        px.bar(df_ms, x="vaccine", y="total", title="Manufacturer share (top 15)"),
        use_container_width=True,
    )
else:
    st.info("No manufacturer data.")
