-- TEARDOWN: permanently removes everything this lab created.
-- Run ONLY in your provided workshop account, after downloading any work you want to keep.
-- Runs as ACCOUNTADMIN: the line below fixes the file's role, which can default to SYSADMIN.
-- Run the entire file. Every statement uses IF EXISTS, so it is safe to rerun.
-- Before running: close Streamlit preview, deployed-app, and notebook tabs.
USE ROLE ACCOUNTADMIN;

-- 1. Database: drops all lab tables (including PAYER_BUDGET and the Time Travel
--    clones), the ENCOUNTER_SUMMARY view, the LAB_DATA stage and its uploaded CSVs,
--    the LAB_CSV file format, and any deployed Encounter Explorer app.
DROP DATABASE IF EXISTS DAY0_LAB;

-- 2. Optional Roles and Access exercise role
DROP ROLE IF EXISTS CARE_TEAM;

-- 3. Notebook services: drops YOUR notebook services (Snowsight creates them in
--    your personal USER$ database). Workshop accounts only: this includes any
--    other notebook services you created in this account.
--    The cleanup query needs a warehouse; LAB_WH is dropped in step 5.
CREATE WAREHOUSE IF NOT EXISTS LAB_WH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60;
USE WAREHOUSE LAB_WH;
SHOW SERVICES OF TYPE NOTEBOOK;
DECLARE
  c CURSOR FOR SELECT "database_name" AS db, "schema_name" AS sch, "name" AS svc
    FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
    WHERE "database_name" = 'USER$' || CURRENT_USER();
BEGIN
  FOR r IN c DO
    EXECUTE IMMEDIATE 'DROP SERVICE IF EXISTS "' || r.db || '"."' || r.sch || '"."' || r.svc || '"';
  END FOR;
  RETURN 'Notebook services dropped';
END;
ALTER ACCOUNT UNSET NOTEBOOK_VNEXT_IDLE_TIMEOUT_OPTIONS_MINUTES;

-- 4. Streamlit compute: clear the account default, stop remaining services, drop the pool
ALTER ACCOUNT UNSET DEFAULT_STREAMLIT_COMPUTE_POOL;
ALTER COMPUTE POOL IF EXISTS LAB_STREAMLIT_POOL STOP ALL;
DROP COMPUTE POOL IF EXISTS LAB_STREAMLIT_POOL;

-- 5. Query warehouse: clear your user default, then drop it
ALTER USER UNSET DEFAULT_WAREHOUSE;
DROP WAREHOUSE IF EXISTS LAB_WH;

-- 6. Git integration: the snowcamp workspace can no longer sync after this.
--    Delete the snowcamp workspace from Projects > Workspaces separately.
DROP API INTEGRATION IF EXISTS SNOWCAMP_GIT_INTEGRATION;

-- Check: all results should be empty
SHOW DATABASES LIKE 'DAY0_LAB';
SHOW COMPUTE POOLS LIKE 'LAB_STREAMLIT_POOL';
SHOW WAREHOUSES LIKE 'LAB_WH';
SHOW ROLES LIKE 'CARE_TEAM';
SHOW API INTEGRATIONS LIKE 'SNOWCAMP_GIT_INTEGRATION';
SHOW SERVICES OF TYPE NOTEBOOK;
