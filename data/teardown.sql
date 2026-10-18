-- TEARDOWN: permanently removes everything this lab created.
-- Run ONLY in your provided workshop account, after downloading any work you want to keep.
-- Keep ACCOUNTADMIN selected from the initial lab setup; this script does not switch roles.
-- Run the entire file. Every statement uses IF EXISTS, so it is safe to rerun.
-- Before running: close Streamlit preview and deployed-app tabs, and suspend
-- the Time Travel notebook service from its Connected menu.

-- 1. Database: drops all lab tables (including PAYER_BUDGET and the Time Travel
--    clones), the ENCOUNTER_SUMMARY view, the LAB_DATA stage and its uploaded CSVs,
--    the LAB_CSV file format, and any deployed Encounter Explorer app.
DROP DATABASE IF EXISTS DAY0_LAB;

-- 2. Optional Roles and Access exercise role
DROP ROLE IF EXISTS CARE_TEAM;

-- 3. Streamlit compute: clear the account default, stop remaining services, drop the pool
ALTER ACCOUNT UNSET DEFAULT_STREAMLIT_COMPUTE_POOL;
ALTER COMPUTE POOL IF EXISTS LAB_STREAMLIT_POOL STOP ALL;
DROP COMPUTE POOL IF EXISTS LAB_STREAMLIT_POOL;

-- 4. Query warehouse: clear your user default, then drop it
ALTER USER UNSET DEFAULT_WAREHOUSE;
DROP WAREHOUSE IF EXISTS LAB_WH;

-- 5. Git integration: the snowcamp workspace can no longer sync after this.
--    Delete the snowcamp workspace from Projects > Workspaces separately if wanted.
DROP API INTEGRATION IF EXISTS SNOWCAMP_GIT_INTEGRATION;

-- Check: all results should be empty
SHOW DATABASES LIKE 'DAY0_LAB';
SHOW COMPUTE POOLS LIKE 'LAB_STREAMLIT_POOL';
SHOW WAREHOUSES LIKE 'LAB_WH';
SHOW ROLES LIKE 'CARE_TEAM';
SHOW API INTEGRATIONS LIKE 'SNOWCAMP_GIT_INTEGRATION';
