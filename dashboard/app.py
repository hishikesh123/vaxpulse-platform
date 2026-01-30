import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ----------------------------
# Config
# ----------------------------
st.set_page_config(page_title="VaxPulse — Dashboard", layout="wide")

API = os.getenv("API_URL", "").rstrip("/")  # optional: if you want to pull real data

session = requests.Session()

def _get_json(path: str):
    """Safe API call (optional)."""
    if not API:
        raise RuntimeError("API_URL not set")
    url = f"{API}{path}"
    r = session.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

# ----------------------------
# Styles (Admin Dashboard look)
# ----------------------------
st.markdown(
    """
<style>
/* Global background */
.stApp {
  background: #eaf3f2;
}

/* Remove default streamlit padding a bit */
.block-container {
  padding-top: 1.2rem;
  padding-bottom: 1.2rem;
}

/* Faux left sidebar */
.vx-sidebar {
  background: #1f2230;
  border-radius: 18px;
  padding: 18px 10px;
  height: calc(100vh - 3rem);
  position: sticky;
  top: 1rem;
}
.vx-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  margin: 10px auto;
  color: #c7cbd8;
  font-size: 20px;
}
.vx-icon.active {
  background: rgba(255, 127, 92, 0.15);
  color: #ff7f5c;
}
.vx-icon:hover {
  background: rgba(255,255,255,0.06);
}

/* Topbar */
.vx-topbar {
  background: #ffffff;
  border-radius: 18px;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 6px 20px rgba(0,0,0,0.04);
  margin-bottom: 16px;
}
.vx-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  color: #1f2230;
}
.vx-badge {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #1f2230;
  color: #ff7f5c;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}
.vx-search {
  flex: 1;
  margin: 0 18px;
  background: #f2f6f6;
  border-radius: 999px;
  padding: 8px 14px;
  color: #667085;
  font-size: 14px;
}
.vx-right {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1f2230;
  font-weight: 600;
}
.vx-pill {
  background: #f2f6f6;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 13px;
}

/* KPI cards */
.vx-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}
.vx-card {
  background: #fff;
  border-radius: 18px;
  padding: 14px 16px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.04);
}
.vx-card h4 {
  margin: 0;
  color: #1f2230;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.85;
}
.vx-card .vx-value {
  margin-top: 6px;
  font-size: 26px;
  font-weight: 800;
  color: #1f2230;
}
.vx-card .vx-delta {
  margin-top: 6px;
  font-size: 12px;
  color: #2e7d32;
}
.vx-card .vx-delta.neg {
  color: #c62828;
}

/* Content layout */
.vx-grid {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 14px;
}
.vx-mini {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
.vx-mini-card-title {
  font-weight: 700;
  color: #1f2230;
  margin-bottom: 6px;
}
.vx-muted {
  color: #667085;
  font-size: 12px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# Demo data (replace with API later)
# ----------------------------
# Monthly totals + growth (fake but realistic)
months = pd.date_range("2023-01-01", "2023-12-01", freq="MS")
totals = pd.Series([100, 140, 210, 260, 340, 410, 560, 530, 590, 650, 620, 720], index=months)
df_mg = pd.DataFrame({"month": months, "total": totals.values})
df_mg["growth_rate"] = df_mg["total"].pct_change()

# Manufacturer totals (fake)
df_ms = pd.DataFrame(
    {"vaccine": ["Pfizer", "Moderna", "AZ", "Sinovac", "J&J"], "total": [500, 300, 220, 180, 120]}
)

# Bar chart demo (orders-like)
df_orders = pd.DataFrame({"month": months.strftime("%b"), "orders": [120, 240, 260, 210, 320, 410, 520, 480, 300, 460, 380, 520]})

# ----------------------------
# Layout (Sidebar + Main)
# ----------------------------
sidebar_col, main_col = st.columns([0.12, 0.88], vertical_alignment="top")

with sidebar_col:
    st.markdown(
        """
<div class="vx-sidebar">
  <div class="vx-icon">☰</div>
  <div class="vx-icon active">🏠</div>
  <div class="vx-icon">✉️</div>
  <div class="vx-icon">❤️</div>
  <div class="vx-icon">⭐</div>
  <div class="vx-icon">📍</div>
  <div class="vx-icon">📈</div>
  <div class="vx-icon">⚙️</div>
</div>
""",
        unsafe_allow_html=True,
    )

with main_col:
    # Topbar
    st.markdown(
        f"""
<div class="vx-topbar">
  <div class="vx-brand">
    <div class="vx-badge">V</div>
    <div>VaxPulse</div>
  </div>
  <div class="vx-search">🔎  Search…</div>
  <div class="vx-right">
    <div class="vx-pill">🔔 10</div>
    <div class="vx-pill">?</div>
    <div class="vx-pill">👤 Bethany</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # KPI cards
    total_traffic = 325_456
    new_users = 3_006
    performance = 0.60
    sales = 852

    st.markdown(
        f"""
<div class="vx-kpi-row">
  <div class="vx-card">
    <h4>Total traffic</h4>
    <div class="vx-value">{total_traffic:,}</div>
    <div class="vx-delta">+5% since last month</div>
  </div>
  <div class="vx-card">
    <h4>New users</h4>
    <div class="vx-value">{new_users:,}</div>
    <div class="vx-delta neg">-4.5% since last month</div>
  </div>
  <div class="vx-card">
    <h4>Performance</h4>
    <div class="vx-value">{int(performance*100)}%</div>
    <div class="vx-delta">+2.5% since last month</div>
  </div>
  <div class="vx-card">
    <h4>Sales</h4>
    <div class="vx-value">{sales:,}</div>
    <div class="vx-delta">+6.5% since last month</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Two-column main grid (left widgets + main charts)
    st.markdown('<div class="vx-grid">', unsafe_allow_html=True)
    left_panel, right_panel = st.columns([0.34, 0.66], vertical_alignment="top")

    with left_panel:
        # Mini cards stack
        st.markdown('<div class="vx-mini">', unsafe_allow_html=True)

        st.markdown(
            """
<div class="vx-card">
  <div class="vx-mini-card-title">Health care</div>
  <div class="vx-muted">Quick link / status module</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
<div class="vx-card">
  <div class="vx-mini-card-title">Weather updates</div>
  <div class="vx-muted">Optional: show API health or data freshness</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
<div class="vx-card" style="text-align:center; padding: 22px 16px;">
  <div style="font-size:44px;">⬇️</div>
  <div class="vx-mini-card-title" style="margin-top:10px;">Updates</div>
  <div class="vx-muted">Deployment + ingestion status</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with right_panel:
        # Line chart: totals
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown('<div class="vx-card">', unsafe_allow_html=True)
            fig_total = px.line(df_mg, x="month", y="total", title="Total vaccinations (month-end)")
            fig_total.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
            st.plotly_chart(fig_total, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with chart_col2:
            st.markdown('<div class="vx-card">', unsafe_allow_html=True)
            fig_growth = px.line(df_mg.dropna(), x="month", y="growth_rate", title="Growth rate (MoM)")
            fig_growth.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
            st.plotly_chart(fig_growth, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Bar chart panel (orders-like)
        st.markdown('<div class="vx-card" style="margin-top:14px;">', unsafe_allow_html=True)
        fig_orders = px.bar(df_orders, x="month", y="orders", title="Total orders (example bar module)")
        fig_orders.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
        st.plotly_chart(fig_orders, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Manufacturer share
        st.markdown('<div class="vx-card" style="margin-top:14px;">', unsafe_allow_html=True)
        fig_manu = px.bar(df_ms, x="vaccine", y="total", title="Top manufacturers (latest snapshot)")
        fig_manu.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
        st.plotly_chart(fig_manu, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.caption(f"© {datetime.now().year} VaxPulse — Demo UI. Wire API_URL to show live data.")
