import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="VaxPulse — Dashboard", layout="wide")
st.title("VaxPulse — Vaccination Dashboard")

session = requests.Session()

def _get_json(path: str):
    r = session.get(f"{API}{path}", timeout=25)
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=600)
def fetch_countries():
    return _get_json("/countries")

@st.cache_data(ttl=300)
def fetch_monthly_growth(country: str):
    return _get_json(f"/kpi/monthly-growth/{country}")

@st.cache_data(ttl=300)
def fetch_manufacturer_share(country: str):
    return _get_json(f"/kpi/manufacturer-share/{country}")

# New endpoints (we'll add in API)
@st.cache_data(ttl=300)
def fetch_kpi_summary(country: str):
    # {"latest_total":..., "latest_growth_rate":..., "peak_growth_rate":..., "as_of": "..."}
    return _get_json(f"/kpi/summary/{country}")

@st.cache_data(ttl=300)
def fetch_world_map(metric: str, as_of: str | None = None):
    # [{"country": "...", "iso_code":"AUS", "value": 0.52}, ...]
    q = f"/map/world?metric={metric}"
    if as_of:
        q += f"&as_of={as_of}"
    return _get_json(q)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.caption("API URL")
    st.code(API)

try:
    countries = fetch_countries()
except Exception as e:
    st.error(f"API not reachable: {e}")
    st.stop()

country = st.sidebar.selectbox("Select country", countries)

tabs = st.tabs([
    "Campaign Status Report",
    "Key Operational Indicators",
    "Country Comparison",
    "Manufacturer",
    "Data Quality"
])

# ---------------- Tab 1: Campaign Status Report ----------------
with tabs[0]:
    st.subheader(f"Campaign Status — {country}")

    # KPI tiles (summary endpoint)
    summary = None
    try:
        summary = fetch_kpi_summary(country)
    except Exception:
        summary = None

    k1, k2, k3, k4 = st.columns(4)
    if summary:
        k1.metric("Total vaccinations (latest)", f"{summary.get('latest_total', 0):,}")
        gr = summary.get("latest_growth_rate")
        k2.metric("MoM growth (latest)", f"{gr*100:.1f}%" if gr is not None else "—")
        peak = summary.get("peak_growth_rate")
        k3.metric("Peak MoM growth", f"{peak*100:.1f}%" if peak is not None else "—")
        k4.metric("As of", summary.get("as_of", "—"))
    else:
        k1.metric("Total vaccinations (latest)", "—")
        k2.metric("MoM growth (latest)", "—")
        k3.metric("Peak MoM growth", "—")
        k4.metric("As of", "—")

    # Trends
    mg = pd.DataFrame(fetch_monthly_growth(country))
    if not mg.empty:
        mg["month"] = pd.to_datetime(mg["month"])
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(
                px.line(mg, x="month", y="total", title="Total vaccinations (month-end)"),
                use_container_width=True
            )
        with c2:
            mg2 = mg.dropna(subset=["growth_rate"])
            st.plotly_chart(
                px.line(mg2, x="month", y="growth_rate", title="Growth rate (MoM)"),
                use_container_width=True
            )
    else:
        st.info("No monthly series available for this country.")

    # Simple funnel (example derived from last month totals)
    # You can replace with real dose-stage metrics if your DB has them.
    if not mg.empty:
        latest_total = int(mg.sort_values("month")["total"].dropna().tail(1).iloc[0])
        funnel = pd.DataFrame({
            "stage": ["Registered (proxy)", "1+ dose (proxy)", "Fully vaccinated (proxy)", "Boosted (proxy)"],
            "value": [latest_total, int(latest_total*0.92), int(latest_total*0.78), int(latest_total*0.55)]
        })
        st.plotly_chart(
            px.bar(funnel, x="stage", y="value", title="Vaccination campaign funnel (proxy)"),
            use_container_width=True
        )

# ---------------- Tab 2: Key Operational Indicators ----------------
with tabs[1]:
    st.subheader("Key Operational Indicators")
    st.caption("Add operational KPIs (dose per 100, boosters %, rolling avg, etc.)")

    mg = pd.DataFrame(fetch_monthly_growth(country))
    if not mg.empty:
        mg["month"] = pd.to_datetime(mg["month"])
        mg["rolling_3m_growth"] = mg["growth_rate"].rolling(3).mean()

        st.plotly_chart(
            px.line(mg.dropna(subset=["rolling_3m_growth"]), x="month", y="rolling_3m_growth",
                    title="Rolling 3-month growth rate"),
            use_container_width=True
        )

# ---------------- Tab 3: Country Comparison (World map + top countries) ----------------
with tabs[2]:
    st.subheader("Country Comparison (World)")

    metric = st.selectbox(
        "Metric",
        ["latest_total_vaccinations", "latest_mom_growth_rate"],
        index=0
    )

    # world choropleth (requires /map/world)
    try:
        wm = pd.DataFrame(fetch_world_map(metric))
        if not wm.empty:
            fig = px.choropleth(
                wm,
                locations="iso_code",
                color="value",
                hover_name="country",
                title="World map",
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=520)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(wm.sort_values("value", ascending=False).head(15), use_container_width=True)
        else:
            st.info("World map data is empty.")
    except Exception as e:
        st.info("World map endpoint not available yet. Add `/map/world` in API.")
        st.caption(f"Details: {e}")

# ---------------- Tab 4: Manufacturer ----------------
with tabs[3]:
    st.subheader(f"Manufacturer — {country}")

    ms = pd.DataFrame(fetch_manufacturer_share(country))
    if not ms.empty:
        st.plotly_chart(
            px.bar(ms, x="vaccine", y="total", title="Top manufacturers (latest snapshot)"),
            use_container_width=True
        )
    else:
        st.info("No manufacturer data for this country.")

# ---------------- Tab 5: Data Quality ----------------
with tabs[4]:
    st.subheader("Data Quality")
    st.caption("Show missing months, null rates, ingestion timestamp, etc.")
    st.write("Add `/quality/summary/{country}` to power this tab.")
