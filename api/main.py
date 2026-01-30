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
    r = session.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

# ----------------- API wrappers -----------------
@st.cache_data(ttl=600)
def fetch_countries():
    return _get_json("/countries")

@st.cache_data(ttl=300)
def fetch_monthly_growth(country: str):
    return _get_json(f"/kpi/monthly-growth/{country}")

@st.cache_data(ttl=300)
def fetch_manufacturer_share(country: str):
    return _get_json(f"/kpi/manufacturer-share/{country}")

# Optional new endpoints (dashboard will still work if they 404)
@st.cache_data(ttl=600)
def fetch_meta_last_updated(country: str | None = None):
    # Expect: {"country": "...", "last_updated": "YYYY-MM-DD"} or {"last_updated": "..."}
    try:
        if country:
            return _get_json(f"/meta/last-updated/{country}")
        return _get_json("/meta/last-updated")
    except Exception:
        return None

@st.cache_data(ttl=600)
def fetch_quality(country: str):
    # Expect: {"country": "...", "months": 48, "missing_months": 2, "null_rate_total": 0.01}
    try:
        return _get_json(f"/quality/summary/{country}")
    except Exception:
        return None


# ----------------- Sidebar -----------------
with st.sidebar:
    st.caption("API status")
    st.code(API)
    st.caption("Tips")
    st.write("- If deployed, set `API_URL` to your public FastAPI URL.")
    st.write("- If charts look wrong, fix aggregation in the API (month-end totals).")

# ----------------- Load countries -----------------
try:
    countries = fetch_countries()
except Exception as e:
    st.error(
        f"Cannot reach FastAPI at **{API}**.\n\n"
        f"Set `API_URL` in your deployment environment to your public API URL.\n\n"
        f"Error: `{e}`"
    )
    st.stop()

# Country selection + comparison
st.subheader("Country selection")
colA, colB = st.columns([2, 3], vertical_alignment="bottom")

with colA:
    country = st.selectbox("Primary country", countries)

with colB:
    compare_mode = st.toggle("Compare countries", value=False)
    compare_countries = []
    if compare_mode:
        compare_countries = st.multiselect(
            "Compare with (max 3)",
            [c for c in countries if c != country],
            default=[],
            max_selections=3
        )

selected_countries = [country] + compare_countries

# ----------------- Fetch data (monthly growth) -----------------
all_mg = []
for c in selected_countries:
    try:
        mg = fetch_monthly_growth(c)
        df = pd.DataFrame(mg)
        if not df.empty:
            df["country"] = c
            df["month"] = pd.to_datetime(df["month"])
            all_mg.append(df)
    except Exception as e:
        st.error(f"Failed to load monthly growth for {c}: {e}")
        st.stop()

df_mg_all = pd.concat(all_mg, ignore_index=True) if all_mg else pd.DataFrame()

if df_mg_all.empty:
    st.warning("No monthly growth data returned by the API.")
    st.stop()

# ----------------- Time range filter -----------------
st.subheader("Time range")
min_month = df_mg_all["month"].min()
max_month = df_mg_all["month"].max()

range_col1, range_col2 = st.columns([3, 2], vertical_alignment="center")
with range_col1:
    start_date, end_date = st.slider(
        "Filter period",
        min_value=min_month.to_pydatetime(),
        max_value=max_month.to_pydatetime(),
        value=(min_month.to_pydatetime(), max_month.to_pydatetime())
    )
with range_col2:
    st.caption("Data window")
    st.write(f"**{pd.to_datetime(start_date).date()} → {pd.to_datetime(end_date).date()}**")

df_mg_f = df_mg_all[
    (df_mg_all["month"] >= pd.to_datetime(start_date)) &
    (df_mg_all["month"] <= pd.to_datetime(end_date))
].copy()

# ----------------- Data freshness (optional) -----------------
meta = fetch_meta_last_updated(country)
if meta and isinstance(meta, dict) and meta.get("last_updated"):
    st.caption(f"🕒 Data last updated (API): **{meta['last_updated']}**")

# ----------------- KPI cards -----------------
st.subheader("Key KPIs")

def _latest_stats(df_country: pd.DataFrame):
    df_country = df_country.sort_values("month")
    latest_row = df_country.dropna(subset=["total"]).tail(1)
    latest_total = int(latest_row["total"].iloc[0]) if not latest_row.empty else None

    latest_growth_row = df_country.dropna(subset=["growth_rate"]).tail(1)
    latest_growth = float(latest_growth_row["growth_rate"].iloc[0]) if not latest_growth_row.empty else None

    peak_growth_row = df_country.dropna(subset=["growth_rate"]).sort_values("growth_rate", ascending=False).head(1)
    peak_growth = float(peak_growth_row["growth_rate"].iloc[0]) if not peak_growth_row.empty else None
    peak_growth_month = peak_growth_row["month"].iloc[0].date().isoformat() if not peak_growth_row.empty else None

    months = df_country["month"].nunique()
    return latest_total, latest_growth, peak_growth, peak_growth_month, months

# show KPIs for primary country only (cleaner)
df_primary = df_mg_f[df_mg_f["country"] == country].copy()
latest_total, latest_growth, peak_growth, peak_month, months = _latest_stats(df_primary)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Country", country)
k2.metric("Latest total (month-end)", f"{latest_total:,}" if latest_total is not None else "—")
k3.metric("Latest MoM growth", f"{latest_growth*100:.1f}%" if latest_growth is not None else "—")
k4.metric("Peak MoM growth", f"{peak_growth*100:.1f}%" if peak_growth is not None else "—")
k5.metric("Months available", f"{months}" if months is not None else "—")

# ----------------- Insight text -----------------
st.subheader("Insights")
insight_lines = []
if peak_growth is not None and peak_month is not None:
    insight_lines.append(f"📈 **Fastest monthly growth** was in **{peak_month}** at **{peak_growth*100:.1f}% MoM**.")
if latest_growth is not None:
    if latest_growth < 0.01:
        insight_lines.append("🟡 Growth appears **low/plateauing** in the most recent months.")
    elif latest_growth > 0.10:
        insight_lines.append("🟢 Recent growth is **strong** compared to typical rollout phases.")
if latest_total is not None:
    insight_lines.append(f"🧾 Latest month-end total is **{latest_total:,} doses**.")

if insight_lines:
    st.write("\n\n".join(insight_lines))
else:
    st.info("Not enough data to generate insights (growth_rate might be null).")

# ----------------- Charts: totals + growth -----------------
st.subheader("Monthly totals and growth")

st.plotly_chart(
    px.line(
        df_mg_f,
        x="month",
        y="total",
        color="country" if compare_mode else None,
        title="Total vaccinations (month-end)"
    ),
    use_container_width=True,
)

# growth chart: drop null growth values for clean plot
df_growth = df_mg_f.dropna(subset=["growth_rate"]).copy()
st.plotly_chart(
    px.line(
        df_growth,
        x="month",
        y="growth_rate",
        color="country" if compare_mode else None,
        title="Growth rate (MoM)"
    ),
    use_container_width=True,
)

# ----------------- Manufacturer chart (primary only) -----------------
st.subheader("Top manufacturers (latest snapshot)")

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

# ----------------- Data quality panel (optional) -----------------
st.subheader("Data quality")
q = fetch_quality(country)
if q:
    qc1, qc2, qc3, qc4 = st.columns(4)
    qc1.metric("Country", q.get("country", country))
    qc2.metric("Months", q.get("months", "—"))
    qc3.metric("Missing months", q.get("missing_months", "—"))
    null_rate = q.get("null_rate_total")
    qc4.metric("Null rate (total)", f"{null_rate*100:.2f}%" if isinstance(null_rate, (int, float)) else "—")
else:
    st.info("Quality endpoint not available yet. Add `/quality/summary/{country}` in the API for this panel.")
