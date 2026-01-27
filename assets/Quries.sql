--Task 1

SELECT country_name AS [Country Name (CN)],
       '29th December 2020' AS [Date 1 (OD1)],
       COALESCE(SUM(CASE WHEN date = '29/12/2020' THEN total_vaccinations END), 0) AS [Vaccine on OD1 (VOD1)],
       '9th January 2021' AS [Date 2 (OD2)],
       COALESCE(SUM(CASE WHEN date = '09/01/2021' THEN total_vaccinations END), 0) AS [Vaccine on OD2 (VOD2)],
       '7th February 2021' AS [Date 3 (OD3)],
       COALESCE(SUM(CASE WHEN date = '07/02/2021' THEN total_vaccinations END), 0) AS [Vaccine on OD3 (VOD3)],
       COALESCE( ( (COALESCE(SUM(CASE WHEN date = '09/01/2021' THEN total_vaccinations END), 0) - COALESCE(SUM(CASE WHEN date = '29/12/2020' THEN total_vaccinations END), 0) ) / NULLIF(COALESCE(SUM(CASE WHEN date = '29/12/2020' THEN total_vaccinations END), 0), 0) * 100), 0) + COALESCE( ( (COALESCE(SUM(CASE WHEN date = '07/02/2021' THEN total_vaccinations END), 0) - COALESCE(SUM(CASE WHEN date = '09/01/2021' THEN total_vaccinations END), 0) ) / NULLIF(COALESCE(SUM(CASE WHEN date = '09/01/2021' THEN total_vaccinations END), 0), 0) * 100), 0) AS [Percentage change of totals]
  FROM Vaccination_by_manu
 WHERE date IN ('29/12/2020', '09/01/2021', '07/02/2021') 
 GROUP BY country_name
 ORDER BY "Percentage change of totals" DESC;

-- Task 2

SELECT g.country_name AS [Country Name],
       g.Month AS Month,
       g.Year AS Year,
       g.cumulative_doses,
       g.GR,
       ga.avg_global_GR,
       (g.GR - ga.avg_global_GR) AS [Difference of GR to Global Average]
  FROM (
           SELECT country_name,
                  substr(date, 7, 4) AS Year,
                  substr(date, 4, 2) AS Month,
                  SUM(total_vaccinations) AS cumulative_doses,
                  (SUM(total_vaccinations) - LAG(SUM(total_vaccinations) ) OVER (PARTITION BY country_name ORDER BY substr(date, 7, 4),
                                             substr(date, 4, 2) ) ) / NULLIF(LAG(SUM(total_vaccinations) ) OVER (PARTITION BY country_name ORDER BY substr(date, 7, 4),
                                                                             substr(date, 4, 2) ), 0) AS GR
             FROM Vaccination_by_manu
            GROUP BY country_name,
                     Year,
                     Month
       )
       AS g
       JOIN
       (
           SELECT substr(date, 7, 4) AS Year,
                  substr(date, 4, 2) AS Month,
                  AVG(GR) AS avg_global_GR
             FROM (
                      SELECT date,
                             substr(date, 7, 4) AS Year,
                             substr(date, 4, 2) AS Month,
                             (SUM(total_vaccinations) - LAG(SUM(total_vaccinations) ) OVER (ORDER BY substr(date, 7, 4),
                                                        substr(date, 4, 2) ) ) / NULLIF(LAG(SUM(total_vaccinations) ) OVER (ORDER BY substr(date, 7, 4),
                                                                                        substr(date, 4, 2) ), 0) AS GR
                        FROM Vaccination_by_manu
                       GROUP BY Year,
                                Month
                  )
                  AS GlobalGR
            GROUP BY Year,
                     Month
       )
       AS ga ON g.Year = ga.Year AND 
                g.Month = ga.Month
 WHERE g.GR > ga.avg_global_GR
 ORDER BY g.Year,
          g.Month,
          g.GR DESC;

-- Task 3

SELECT "Vaccine Type",
       "Country",
       "Percentage of vaccine type"
  FROM (
           SELECT vbm.vaccine AS [Vaccine Type],
                  vbm.country_name AS Country,
                  (vbm.total_vaccinations * 1.0 / ct.total_vaccinations_country) * 100 AS [Percentage of vaccine type],
                  ROW_NUMBER() OVER (PARTITION BY vbm.country_name ORDER BY (vbm.total_vaccinations * 1.0 / ct.total_vaccinations_country) DESC) AS rank
             FROM Vaccination_by_manu vbm
                  JOIN
                  (
                      SELECT country_name,
                             SUM(total_vaccinations) AS total_vaccinations_country
                        FROM Vaccination_by_manu
                       GROUP BY country_name
                  )
                  ct ON vbm.country_name = ct.country_name
       )
       AS VaccineShare
 WHERE rank <= 5
 ORDER BY "Percentage of vaccine type" DESC
 LIMIT 5;

-- Task 4

SELECT country_name AS [Country Name],
       SUBSTR(date, 7, 4) || '-' || SUBSTR(date, 4, 2) AS Month,-- Convert dd/mm/yyyy to yyyy-mm
       source_url AS [Source Name (URL)],
       SUM(total_vaccinated) AS [Total Administered Vaccines]
  FROM Country_data
 GROUP BY country_name,
          SUBSTR(date, 7, 4) || '-' || SUBSTR(date, 4, 2),-- Group by formatted date
          source_url
 ORDER BY "Total Administered Vaccines" DESC;

-- Task 5

SELECT date AS Date,
       vaccine AS [Vaccine Type],
       COALESCE(MAX(CASE WHEN rank = 1 THEN "Fully Vaccinated People" END), 0) AS [Fully Vaccinated people in Top 1 country],
       COALESCE(MAX(CASE WHEN rank = 2 THEN "Fully Vaccinated People" END), 0) AS [Fully Vaccinated people in Top 2 country],
       COALESCE(MAX(CASE WHEN rank = 3 THEN "Fully Vaccinated People" END), 0) AS [Fully Vaccinated people in Top 3 country]
  FROM (
           SELECT date,
                  vaccine,
                  country_name AS Country,
                  people_fully_vaccinated AS [Fully Vaccinated People],
                  ROW_NUMBER() OVER (PARTITION BY date,
                  vaccine ORDER BY people_fully_vaccinated DESC) AS rank
             FROM Country_data
            WHERE SUBSTR(date, 7, 4) IN ('2022', '2023')-- Filter for years 2022 and 2023 
       )
       AS RankedCountries
 WHERE rank <= 3
 GROUP BY date,
          vaccine
 ORDER BY date,
          vaccine;

    
