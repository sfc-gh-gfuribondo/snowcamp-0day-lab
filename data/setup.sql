-- =====================================================================
-- Snowflake Day 0 Lab - setup.sql
-- Part A: run this in Module 3 BEFORE uploading the CSV files.
-- Part B: OPTIONAL fallback - only if the CSV upload does not work.
-- =====================================================================

-- ---------- Part A: warehouse, database, empty tables ----------------
USE ROLE SYSADMIN;

CREATE WAREHOUSE IF NOT EXISTS LAB_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60          -- seconds idle before it pauses (saves credits)
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS DAY0_LAB;
CREATE SCHEMA IF NOT EXISTS DAY0_LAB.HEALTHCARE;

USE WAREHOUSE LAB_WH;
USE SCHEMA DAY0_LAB.HEALTHCARE;

CREATE OR REPLACE TABLE PATIENTS (
  PATIENT_ID        VARCHAR,
  FIRST_NAME        VARCHAR,
  LAST_NAME         VARCHAR,
  BIRTHDATE         DATE,
  GENDER            VARCHAR,
  RACE              VARCHAR,
  CITY              VARCHAR,
  COUNTY            VARCHAR,
  STATE             VARCHAR,
  INCOME            NUMBER(10,0),
  PAYER             VARCHAR,
  PRIMARY_CONDITION VARCHAR
);

CREATE OR REPLACE TABLE ENCOUNTERS (
  ENCOUNTER_ID    VARCHAR,
  PATIENT_ID      VARCHAR,
  START_TS        TIMESTAMP_NTZ,
  STOP_TS         TIMESTAMP_NTZ,
  ENCOUNTER_CLASS VARCHAR,
  DESCRIPTION     VARCHAR,
  TOTAL_COST      NUMBER(12,2),
  PAYER_COVERAGE  NUMBER(12,2)
);

CREATE OR REPLACE TABLE CLINICAL_NOTES (
  NOTE_ID      VARCHAR,
  PATIENT_ID   VARCHAR,
  ENCOUNTER_ID VARCHAR,
  NOTE_DATE    DATE,
  NOTE_TYPE    VARCHAR,
  NOTE_TEXT    VARCHAR
);

-- ---------- Part B: OPTIONAL fallback (no upload needed) -------------
-- Fills the three tables with generated rows of the same shape and
-- row counts (500 / 5,000 / 1,500). Values differ from the CSVs, so
-- your query results will not match the screenshots exactly.
-- Select from here to the end of the file and run it.

INSERT INTO PATIENTS
SELECT
  'P' || LPAD(SEQ4() + 1, 4, '0'),
  ARRAY_CONSTRUCT('Maria','James','Aisha','Carlos','Mei','Wei','Olivia','Omar')[UNIFORM(0, 7, RANDOM())]::VARCHAR,
  ARRAY_CONSTRUCT('Smith','Garcia','Nguyen','Patel','Kim','Lopez','Chen','Rivera')[UNIFORM(0, 7, RANDOM())]::VARCHAR,
  DATEADD(day, UNIFORM(0, 30000, RANDOM()), '1935-01-01'::DATE),
  IFF(UNIFORM(0, 1, RANDOM()) = 0, 'F', 'M'),
  ARRAY_CONSTRUCT('white','black','asian','hispanic','other')[UNIFORM(0, 4, RANDOM())]::VARCHAR,
  ARRAY_CONSTRUCT('Boston','Worcester','Springfield','Cambridge','Lowell')[UNIFORM(0, 4, RANDOM())]::VARCHAR,
  'Middlesex',
  'MA',
  UNIFORM(15, 199, RANDOM()) * 1000,
  ARRAY_CONSTRUCT('Medicare','Medicaid','Blue Cross','Aetna','UnitedHealthcare','No Insurance')[UNIFORM(0, 5, RANDOM())]::VARCHAR,
  ARRAY_CONSTRUCT('type 2 diabetes','hypertension','asthma','COPD','heart failure','none')[UNIFORM(0, 5, RANDOM())]::VARCHAR
FROM TABLE(GENERATOR(ROWCOUNT => 500));

INSERT INTO ENCOUNTERS
WITH g AS (
  SELECT
    SEQ4() + 1 AS n,
    ARRAY_CONSTRUCT('wellness','wellness','ambulatory','ambulatory','outpatient',
                    'urgentcare','emergency','inpatient')[UNIFORM(0, 7, RANDOM())]::VARCHAR AS cls,
    DATEADD(minute, UNIFORM(0, 1576800, RANDOM()), '2023-01-01'::TIMESTAMP_NTZ) AS st
  FROM TABLE(GENERATOR(ROWCOUNT => 5000))
)
SELECT
  'E' || LPAD(n, 5, '0'),
  'P' || LPAD(UNIFORM(1, 500, RANDOM()), 4, '0'),
  st,
  DATEADD(hour, IFF(cls = 'inpatient', 72, 2), st),
  cls,
  INITCAP(cls) || ' visit',
  CASE cls WHEN 'inpatient' THEN 15000 WHEN 'emergency' THEN 2500 WHEN 'outpatient' THEN 900 ELSE 200 END
    * UNIFORM(50, 150, RANDOM()) / 100,
  0
FROM g;

UPDATE ENCOUNTERS SET PAYER_COVERAGE = ROUND(TOTAL_COST * 0.7, 2);

INSERT INTO CLINICAL_NOTES
SELECT
  'N' || LPAD(ROW_NUMBER() OVER (ORDER BY ENCOUNTER_ID), 5, '0'),
  PATIENT_ID,
  ENCOUNTER_ID,
  START_TS::DATE,
  'SOAP',
  'S: Patient seen for ' || LOWER(DESCRIPTION) || '. O: Vitals stable. A: Routine follow-up. P: Continue current plan.'
FROM ENCOUNTERS
SAMPLE (1500 ROWS);

SELECT 'PATIENTS' AS table_name, COUNT(*) AS row_count FROM PATIENTS
UNION ALL SELECT 'ENCOUNTERS', COUNT(*) FROM ENCOUNTERS
UNION ALL SELECT 'CLINICAL_NOTES', COUNT(*) FROM CLINICAL_NOTES;
