-- Run after setup.sql and uploading all three CSVs to the LAB_DATA stage root.
USE ROLE SYSADMIN;
USE WAREHOUSE LAB_WH;
USE SCHEMA DAY0_LAB.HEALTHCARE;
LIST @LAB_DATA;

-- Default load history skips unchanged files already loaded. Do not add FORCE=TRUE.
COPY INTO PATIENTS FROM @LAB_DATA
  FILES = ('patients.csv') FILE_FORMAT = (FORMAT_NAME = 'LAB_CSV')
  ON_ERROR = 'ABORT_STATEMENT';
COPY INTO ENCOUNTERS FROM @LAB_DATA
  FILES = ('encounters.csv') FILE_FORMAT = (FORMAT_NAME = 'LAB_CSV')
  ON_ERROR = 'ABORT_STATEMENT';
COPY INTO CLINICAL_NOTES FROM @LAB_DATA
  FILES = ('clinical_notes.csv') FILE_FORMAT = (FORMAT_NAME = 'LAB_CSV')
  ON_ERROR = 'ABORT_STATEMENT';

SELECT 'PATIENTS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM PATIENTS
UNION ALL SELECT 'ENCOUNTERS', COUNT(*) FROM ENCOUNTERS
UNION ALL SELECT 'CLINICAL_NOTES', COUNT(*) FROM CLINICAL_NOTES;
-- Expected: 500 / 5000 / 1500. If a COPY fails, stop, correct the upload,
-- and rerun this file. The successfully loaded unchanged files are skipped.
-- If uploads remain blocked, use fallback_data.sql instead; it resets all
-- three lab tables to the exact downloadable dataset. Do not combine paths.
