-- Creating Location table
CREATE TABLE Location (
    country_name TEXT PRIMARY KEY,
    last_observation_date TEXT,
    source_name TEXT,
    source_url TEXT
);

-- Creating Country_data table
CREATE TABLE Country_data (
    date TEXT,
    vaccine TEXT,
    source_url TEXT,
    total_vaccinated INTEGER,
    people_vaccinated INTEGER,
    people_fully_vaccinated INTEGER,
    total_boosters INTEGER,
    country_name TEXT,
    PRIMARY KEY (date, vaccine),
    FOREIGN KEY (country_name) REFERENCES Location (country_name)
);

-- Creating Vaccination table
CREATE TABLE Vaccination (
    date TEXT,
    location TEXT,
    total_vaccination INTEGER,
    people_vaccinated INTEGER,
    people_fully_vaccinated INTEGER,
    total_boosters INTEGER,
    daily_vaccinations_raw INTEGER,
    daily_vaccination INTEGER,
    total_vaccination_per_hundred REAL,
    people_vaccinated_per_hundred REAL,
    people_fully_vaccinated_per_hundred REAL,
    daily_vaccination_per_million REAL,
    daily_people_vaccinated INTEGER,
    daily_people_vaccinated_per_hundred REAL,
    PRIMARY KEY (date, location),
    FOREIGN KEY (location) REFERENCES Location (country_name)
);

-- Creating Vaccination_age_group table
CREATE TABLE Vaccination_age_group (
    date TEXT,
    age_group TEXT,
    people_vaccinated_per_hundred REAL,
    people_fully_vaccinated_per_hundred REAL,
    people_with_booster_per_hundred REAL,
    country_name TEXT,
    PRIMARY KEY (date, age_group),
    FOREIGN KEY (country_name) REFERENCES Location (country_name)
);

-- Creating Vaccination_by_manu table
CREATE TABLE Vaccination_by_manu (
    date TEXT,
    vaccine TEXT,
    total_vaccinations INTEGER,
    country_name TEXT,
    PRIMARY KEY (date, vaccine),
    FOREIGN KEY (country_name) REFERENCES Location (country_name)
);
