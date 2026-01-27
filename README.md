# VaxPulse: Public Health Vaccination Analytics Warehouse

## Overview

This repository presents an **industry-oriented database design and analytics project** based on the *Our World in Data – Global COVID-19 Vaccinations* dataset. The project goes beyond a typical academic submission by emphasising **clean relational modelling, third normal form (3NF) compliance, reproducible SQL pipelines, and insight-driven analytical queries with visualisations**.

The work was originally developed as part of an RMIT University database concepts course and has been **refactored for portfolio use**, aligning with real-world data engineering and analytics expectations.

---

## Objectives

* Design a **normalised relational database** from a complex, real-world public health dataset
* Translate conceptual models into a **production-ready relational schema**
* Implement the database using **SQLite** with integrity constraints
* Import and restructure raw CSV data to fit the designed schema
* Develop **advanced analytical SQL queries** to answer policy-relevant questions
* Communicate insights through **clear, decision-oriented visualisations**

---

## Dataset

The project uses selected files from the *Our World in Data COVID-19 Vaccinations* dataset, which tracks global vaccination rollout metrics such as:

* Total and daily vaccinations
* Fully and partially vaccinated populations
* Vaccine manufacturers and types
* Country-level and time-series observations

**Primary sources:**

* [https://github.com/owid/covid-19-data](https://github.com/owid/covid-19-data)
* [https://www.nature.com/articles/s41562-021-01122-8](https://www.nature.com/articles/s41562-021-01122-8)

---

## Repository Structure

```
.
├── data/
│   ├── raw/                # Original OWID CSV files
│   └── processed/          # Restructured CSVs aligned to database schema
│
├── model/
│   └── Model.pdf           # ER diagram, assumptions, normalisation rationale, schema
│
├── sql/
│   ├── Database.sql        # DDL: tables, keys, constraints
│   └── Queries.sql         # Analytical SQL queries (Tasks D.1–D.5)
│
├── database/
│   └── Vaccinations.db     # Fully populated SQLite database
│
├── visuals/
│   └── Queries.pdf         # Query outputs + charts
│
└── README.md
```

---

## Database Design

### Conceptual Modelling

* ER model created using **UML notation**
* Clear separation of entities such as *Country*, *Vaccination Observation*, *Vaccine Type*, *Manufacturer*, and *Data Source*
* Explicit modelling of **temporal relationships** and **many-to-many associations**

### Normalisation

* Applied step-by-step normalisation from initial design to **3NF**
* Eliminated:

  * Partial dependencies
  * Transitive dependencies
  * Redundant attributes across time-series data
* Improved update integrity and analytical flexibility

### Schema Highlights

* Surrogate primary keys for stability
* Foreign key constraints for referential integrity
* Date-based indexing for time-series performance

---

## Database Implementation

* Implemented using **SQLite** for portability and reproducibility
* Schema created via `Database.sql` (DDL only)
* Data imported using SQLite Studio after CSV restructuring
* Fully self-contained database file: `Vaccinations.db`

---

## Analytical Queries & Insights

The `Queries.sql` file contains advanced analytical queries addressing questions such as:

1. **Cross-date vaccination growth comparison** across countries
2. **Monthly vaccination growth rates** vs global averages
3. **Vaccine manufacturer market share** by country
4. **Data-source-level vaccination totals** by month
5. **Vaccination speed comparisons** across selected countries and years

Each query is:

* Written as a **single SQL statement** (nested where required)
* Optimised for clarity and correctness
* Paired with a **visual explanation** in `Queries.pdf`

---

## Visualisation

* Query outputs are visualised using charts (bar, line, comparative plots)
* Visuals are chosen based on **data semantics**, not convenience
* Emphasis on interpretability for non-technical stakeholders

---

## How to Run

1. Open `Vaccinations.db` in **SQLite Studio**
2. Execute `Database.sql` to review schema (already applied in DB file)
3. Run queries from `Queries.sql`
4. Cross-reference outputs with `Queries.pdf` for visual interpretation

---

## Portfolio Positioning

This project demonstrates:

* Strong **relational modelling fundamentals**
* Practical application of **normalisation theory**
* Ability to translate raw public data into **analytics-ready systems**
* SQL proficiency beyond CRUD (windowing, aggregation, ranking, temporal logic)
* Clear communication of insights through data visualisation

It is suitable for roles involving:

* Data Analyst / BI Analyst
* Junior Data Engineer
* Analytics Consultant
* Database Developer

---

## References

* Our World in Data. *COVID-19 Vaccinations Dataset*
* Mathieu et al. (2021). *A global database of COVID-19 vaccinations*. Nature Human Behaviour

---

## Author

**Hishikesh Phukan**
Master of Data Science — RMIT University
GitHub: [https://github.com/hishikesh123](https://github.com/hishikesh123)

---

> This repository represents a refactored, portfolio-grade version of an academic project. All modelling and queries are original work, based on publicly available data.
