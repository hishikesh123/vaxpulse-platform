-- Monthly totals per country (for growth analytics)
CREATE OR REPLACE VIEW vw_country_monthly_totals AS
SELECT
  location AS country_name,
  date_trunc('month', date)::date AS month,
  MAX(total_vaccination) AS month_end_total_vaccinations
FROM vaccination
GROUP BY location, date_trunc('month', date);

-- Monthly growth rate (MoM) per country
CREATE OR REPLACE VIEW vw_country_monthly_growth AS
SELECT
  country_name,
  month,
  month_end_total_vaccinations,
  (month_end_total_vaccinations
   - LAG(month_end_total_vaccinations) OVER (PARTITION BY country_name ORDER BY month)
  )::double precision
  / NULLIF(LAG(month_end_total_vaccinations) OVER (PARTITION BY country_name ORDER BY month), 0)
  AS growth_rate
FROM vw_country_monthly_totals;
