import os
import sqlite3
import pandas as pd
import psycopg
from datetime import datetime

def parse_ddmmyyyy_to_date(s: str):
    if s is None:
        return None
    # SQLite has dd/mm/yyyy strings
    return datetime.strptime(s, "%d/%m/%Y").date()

def main():
    sqlite_path = os.environ.get("SQLITE_PATH", "assets/Vaccinations.db")
    pg_dsn = os.environ["PG_DSN"]

    sq = sqlite3.connect(sqlite_path)
    pg = psycopg.connect(pg_dsn)

    # Load tables from SQLite
    tables = ["Location", "Vaccination", "Country_data", "Vaccination_age_group", "Vaccination_by_manu"]

    with pg.cursor() as cur:
        # Clear existing (idempotent dev workflow)
        cur.execute("TRUNCATE vaccination_by_manu, vaccination_age_group, country_data, vaccination RESTART IDENTITY;")
        cur.execute("TRUNCATE location RESTART IDENTITY CASCADE;")
        pg.commit()

    # 1) Location
    loc = pd.read_sql_query("SELECT * FROM Location", sq)
    if "last_observation_date" in loc.columns:
        # may already be ISO; if not, leave as text and let Postgres cast best-effort
       loc["last_observation_date"] = pd.to_datetime(
    loc["last_observation_date"], format="%d/%m/%Y", errors="coerce"
).dt.date


    with pg.cursor() as cur:
        for r in loc.itertuples(index=False):
            cur.execute(
                """
                INSERT INTO location(country_name, last_observation_date, source_name, source_url)
                VALUES (%s,%s,%s,%s)
                """,
                (r.country_name, r.last_observation_date, r.source_name, r.source_url),
            )
        pg.commit()

    # 2) Vaccination
    v = pd.read_sql_query("SELECT * FROM Vaccination", sq)
    v["date"] = v["date"].apply(parse_ddmmyyyy_to_date)

    with pg.cursor() as cur:
        for r in v.itertuples(index=False):
            cur.execute(
                """
                INSERT INTO vaccination(
                  date, location, total_vaccination, people_vaccinated, people_fully_vaccinated, total_boosters,
                  daily_vaccinations_raw, daily_vaccination, total_vaccination_per_hundred,
                  people_vaccinated_per_hundred, people_fully_vaccinated_per_hundred, daily_vaccination_per_million,
                  daily_people_vaccinated, daily_people_vaccinated_per_hundred
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    r.date, r.location, r.total_vaccination, r.people_vaccinated, r.people_fully_vaccinated, r.total_boosters,
                    r.daily_vaccinations_raw, r.daily_vaccination, r.total_vaccination_per_hundred,
                    r.people_vaccinated_per_hundred, r.people_fully_vaccinated_per_hundred, r.daily_vaccination_per_million,
                    r.daily_people_vaccinated, r.daily_people_vaccinated_per_hundred
                ),
            )
        pg.commit()

    # 3) Country_data
    cd = pd.read_sql_query("SELECT * FROM Country_data", sq)
    cd["date"] = cd["date"].apply(parse_ddmmyyyy_to_date)

    with pg.cursor() as cur:
        for r in cd.itertuples(index=False):
            cur.execute(
                """
                INSERT INTO country_data(
                  date, vaccine, source_url, total_vaccinated, people_vaccinated, people_fully_vaccinated, total_boosters, country_name
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    r.date, r.vaccine, r.source_url, r.total_vaccinated, r.people_vaccinated, r.people_fully_vaccinated, r.total_boosters, r.country_name
                ),
            )
        pg.commit()

    # 4) Vaccination_age_group
    ag = pd.read_sql_query("SELECT * FROM Vaccination_age_group", sq)
    ag["date"] = ag["date"].apply(parse_ddmmyyyy_to_date)

    with pg.cursor() as cur:
        for r in ag.itertuples(index=False):
            cur.execute(
                """
                INSERT INTO vaccination_age_group(
                  date, age_group, people_vaccinated_per_hundred, people_fully_vaccinated_per_hundred,
                  people_with_booster_per_hundred, country_name
                ) VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (
                    r.date, r.age_group, r.people_vaccinated_per_hundred, r.people_fully_vaccinated_per_hundred,
                    r.people_with_booster_per_hundred, r.country_name
                ),
            )
        pg.commit()

    # 5) Vaccination_by_manu
    bm = pd.read_sql_query("SELECT * FROM Vaccination_by_manu", sq)
    bm["date"] = bm["date"].apply(parse_ddmmyyyy_to_date)

    with pg.cursor() as cur:
        for r in bm.itertuples(index=False):
            cur.execute(
                """
                INSERT INTO vaccination_by_manu(date, vaccine, total_vaccinations, country_name)
                VALUES (%s,%s,%s,%s)
                """,
                (r.date, r.vaccine, r.total_vaccinations, r.country_name),
            )
        pg.commit()

    print("✅ Ingestion complete.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()