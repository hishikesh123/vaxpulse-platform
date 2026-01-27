-- 002_widen_ints.sql
-- Widen large count columns to BIGINT to avoid 32-bit overflow

ALTER TABLE vaccination
  ALTER COLUMN total_vaccination TYPE BIGINT,
  ALTER COLUMN people_vaccinated TYPE BIGINT,
  ALTER COLUMN people_fully_vaccinated TYPE BIGINT,
  ALTER COLUMN total_boosters TYPE BIGINT,
  ALTER COLUMN daily_vaccinations_raw TYPE BIGINT,
  ALTER COLUMN daily_vaccination TYPE BIGINT,
  ALTER COLUMN daily_people_vaccinated TYPE BIGINT;

ALTER TABLE country_data
  ALTER COLUMN total_vaccinated TYPE BIGINT,
  ALTER COLUMN people_vaccinated TYPE BIGINT,
  ALTER COLUMN people_fully_vaccinated TYPE BIGINT,
  ALTER COLUMN total_boosters TYPE BIGINT;

ALTER TABLE vaccination_by_manu
  ALTER COLUMN total_vaccinations TYPE BIGINT;
