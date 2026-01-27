-- 001_init.sql
-- Core schema (PostgreSQL)

CREATE TABLE IF NOT EXISTS location (
  country_name TEXT PRIMARY KEY,
  last_observation_date DATE,
  source_name TEXT,
  source_url TEXT
);

CREATE TABLE IF NOT EXISTS vaccination (
  date DATE NOT NULL,
  location TEXT NOT NULL REFERENCES location(country_name),
  total_vaccination INTEGER CHECK (total_vaccination >= 0),
  people_vaccinated INTEGER CHECK (people_vaccinated >= 0),
  people_fully_vaccinated INTEGER CHECK (people_fully_vaccinated >= 0),
  total_boosters INTEGER CHECK (total_boosters >= 0),
  daily_vaccinations_raw INTEGER CHECK (daily_vaccinations_raw >= 0),
  daily_vaccination INTEGER CHECK (daily_vaccination >= 0),
  total_vaccination_per_hundred DOUBLE PRECISION,
  people_vaccinated_per_hundred DOUBLE PRECISION,
  people_fully_vaccinated_per_hundred DOUBLE PRECISION,
  daily_vaccination_per_million DOUBLE PRECISION,
  daily_people_vaccinated INTEGER CHECK (daily_people_vaccinated >= 0),
  daily_people_vaccinated_per_hundred DOUBLE PRECISION,
  PRIMARY KEY (date, location)
);

-- FIX: include country_name in PK so it's actually unique across countries
CREATE TABLE IF NOT EXISTS country_data (
  date DATE NOT NULL,
  vaccine TEXT NOT NULL,
  source_url TEXT,
  total_vaccinated INTEGER CHECK (total_vaccinated >= 0),
  people_vaccinated INTEGER CHECK (people_vaccinated >= 0),
  people_fully_vaccinated INTEGER CHECK (people_fully_vaccinated >= 0),
  total_boosters INTEGER CHECK (total_boosters >= 0),
  country_name TEXT NOT NULL REFERENCES location(country_name),
  PRIMARY KEY (country_name, date, vaccine)
);

CREATE TABLE IF NOT EXISTS vaccination_age_group (
  date DATE NOT NULL,
  age_group TEXT NOT NULL,
  people_vaccinated_per_hundred DOUBLE PRECISION,
  people_fully_vaccinated_per_hundred DOUBLE PRECISION,
  people_with_booster_per_hundred DOUBLE PRECISION,
  country_name TEXT NOT NULL REFERENCES location(country_name),
  PRIMARY KEY (country_name, date, age_group)
);

CREATE TABLE IF NOT EXISTS vaccination_by_manu (
  date DATE NOT NULL,
  vaccine TEXT NOT NULL,
  total_vaccinations INTEGER CHECK (total_vaccinations >= 0),
  country_name TEXT NOT NULL REFERENCES location(country_name),
  PRIMARY KEY (country_name, date, vaccine)
);

-- Performance indexes (analytics patterns)
CREATE INDEX IF NOT EXISTS idx_vaccination_location_date ON vaccination(location, date);
CREATE INDEX IF NOT EXISTS idx_vbm_date ON vaccination_by_manu(date);
CREATE INDEX IF NOT EXISTS idx_vbm_country ON vaccination_by_manu(country_name);
