import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API = "http://127.0.0.1:8000"

st.title("VaxPulse — Vaccination Analytics Dashboard")

countries = requests.get(f"{API}/countries").json()
country = st.selectbox("Select a country", countries)

st.subheader("Monthly Growth")
mg = requests.get(f"{API}/kpi/monthly-growth/{country}").json()
df_mg = pd.DataFrame(mg)

if not df_mg.empty:
    df_mg["month"] = pd.to_datetime(df_mg["month"])
    st.plotly_chart(px.line(df_mg, x="month", y="total", title="Total vaccinations (month-end)"), use_container_width=True)
    st.plotly_chart(px.line(df_mg, x="month", y="growth_rate", title="Growth rate (MoM)"), use_container_width=True)
else:
    st.info("No data for this country.")

st.subheader("Top Manufacturers (Total doses)")
ms = requests.get(f"{API}/kpi/manufacturer-share/{country}").json()
df_ms = pd.DataFrame(ms)
if not df_ms.empty:
    st.plotly_chart(px.bar(df_ms, x="vaccine", y="total", title="Manufacturer share (top 15)"), use_container_width=True)
else:
    st.info("No manufacturer data.")
