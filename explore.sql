-- Snowflake Foundations: SQL Basics
-- Open this prepopulated file in your private snowcamp workspace.
-- Prerequisite: run data/setup.sql and data/load_data.sql first.
-- Keep ACCOUNTADMIN selected throughout this isolated workshop.
-- Run section 0 first, then select and run one numbered section at a time.
-- Read each result before continuing; do not use Run all for the lesson.

-- 0. Set the context for this SQL file.
USE WAREHOUSE LAB_WH;
USE SCHEMA DAY0_LAB.HEALTHCARE;

-- 1. Look at some rows. LIMIT keeps the preview small.
SELECT * FROM PATIENTS LIMIT 10;

-- 2. Filter and sort. Text values such as 'Boston' are case-sensitive.
SELECT FIRST_NAME, LAST_NAME, CITY, PAYER
FROM PATIENTS
WHERE CITY = 'Boston'
  AND PAYER = 'Medicare'
ORDER BY LAST_NAME;

-- 3. Count and total with GROUP BY.
-- Does the most frequent visit type also have the highest total cost?
SELECT ENCOUNTER_CLASS,
       COUNT(*) AS encounters,
       ROUND(AVG(TOTAL_COST), 2) AS avg_cost,
       SUM(TOTAL_COST) AS total_cost
FROM ENCOUNTERS
GROUP BY ENCOUNTER_CLASS
ORDER BY total_cost DESC;

-- 4. Combine tables with JOIN. The patient ID connects a visit to its payer.
SELECT p.PAYER,
       COUNT(*) AS encounters,
       SUM(e.TOTAL_COST) AS total_cost,
       SUM(e.TOTAL_COST - e.PAYER_COVERAGE) AS patient_out_of_pocket
FROM ENCOUNTERS e
JOIN PATIENTS p ON p.PATIENT_ID = e.PATIENT_ID
GROUP BY p.PAYER
ORDER BY patient_out_of_pocket DESC;

-- 5. Work with dates. Find a month with more visits than the previous month.
SELECT DATE_TRUNC('month', START_TS) AS month,
       COUNT(*) AS encounters
FROM ENCOUNTERS
WHERE ENCOUNTER_CLASS = 'emergency'
GROUP BY month
ORDER BY month;

-- 6. Save a query as a view. The Streamlit app requires this step.
-- This creates/replaces the lab view; it does not change the underlying rows.
CREATE OR REPLACE VIEW ENCOUNTER_SUMMARY AS
SELECT e.ENCOUNTER_ID,
       e.PATIENT_ID,
       p.CITY,
       p.PAYER,
       DATEDIFF('year', p.BIRTHDATE, e.START_TS::DATE)
         - IFF(DATEADD('year', DATEDIFF('year', p.BIRTHDATE, e.START_TS::DATE),
                       p.BIRTHDATE) > e.START_TS::DATE, 1, 0) AS AGE_AT_VISIT,
       e.ENCOUNTER_CLASS,
       e.START_TS::DATE AS VISIT_DATE,
       e.TOTAL_COST,
       e.PAYER_COVERAGE,
       e.TOTAL_COST - e.PAYER_COVERAGE AS OUT_OF_POCKET
FROM ENCOUNTERS e
JOIN PATIENTS p ON p.PATIENT_ID = e.PATIENT_ID;

SELECT * FROM ENCOUNTER_SUMMARY LIMIT 10;

-- 7. Peek under the hood (no additional SQL).
-- Open Monitoring > Query History, choose your query, then Query Profile.

-- Extra practice: add your own queries or reviewed CoCo suggestions below.
-- Keep Time Travel's intentional UPDATE and DROP in time_travel.ipynb.