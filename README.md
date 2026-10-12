# Snowflake Foundations: Day 0 Lab

A 90-minute hands-on introduction for people brand new to Snowflake. Start with a guided Snowsight tour, create a private workspace, load fictional healthcare data, query it with SQL, recover an accidental change with Time Travel, and build a Streamlit app.

**[Open the lab guide](https://sfc-gh-gfuribondo.github.io/snowcamp-0day-lab/)** · **[Download all materials](https://sfc-gh-gfuribondo.github.io/snowcamp-0day-lab/snowcamp-materials.zip)**

No Marketplace installation or local development tools are required for participants.

## Your lab account

Each participant receives a **personal Snowflake trial account** from the facilitator. It remains active for **three days after the lab** so you can revisit exercises and continue practicing.

- Use the supplied account URL and sign-in instructions. Do not create another trial or use a production account.
- Confirm the exact expiration time with your facilitator.
- Download your edited SQL and Python files, including your final app code, before access expires. Keep the original materials ZIP locally.

## Start here

1. Open the [lab guide](https://sfc-gh-gfuribondo.github.io/snowcamp-0day-lab/) and sign in to your provided account in another browser tab.
2. Download and unzip the materials bundle.
3. Follow the Snowsight tour and **create a private workspace named `snowcamp`**. The guide distinguishes the workspace creation control from the **Add new** control used for files.
4. Upload `setup.sql`, `load_data.sql`, and `streamlit_app.py` into that workspace. Create `explore.sql` for practice.
5. Run `setup.sql` to create the lab infrastructure. Upload the three CSVs to the database stage `DAY0_LAB.HEALTHCARE.LAB_DATA`, then run `load_data.sql`.
6. Continue through SQL Basics, Time Travel, and Streamlit. Check the expected results before moving on.

**Code lives in the workspace. CSV files live on the database stage. Loaded rows live in tables.** Uploading a file is not the same as loading table rows.

## Agenda

| Core section | Minutes |
| --- | ---: |
| Lab overview | 3 |
| Snowsight tour and workspace creation | 12 |
| Meet CoCo | 6 |
| Core concepts | 8 |
| Set up and load data | 18 |
| SQL basics | 15 |
| Time Travel | 10 |
| Your first Streamlit app | 15 |
| Wrap-up and next steps | 3 |
| **Total** | **90** |

Optional extensions follow the core wrap-up: **SQL Challenges** (8 minutes) and **Roles and Access** (10 minutes).

Every module includes a collapsible **Try it with CoCo** section with a copyable prompt and a success check. These activities are additional practice, outside the 90-minute core timing.

## Data and loading paths

The dataset is independently generated fictional teaching data, **not real patient data and not an export of Synthea**. It is not intended for clinical decisions or conclusions about real healthcare populations.

| File | Rows | Purpose |
| --- | ---: | --- |
| `data/patients.csv` | 500 | Patient demographics and teaching attributes |
| `data/encounters.csv` | 5,000 | Visits, costs, and payer coverage |
| `data/clinical_notes.csv` | 1,500 | Templated fictional clinical notes |

### Normal path

Run `data/setup.sql`, upload the CSVs to the `LAB_DATA` stage root through Snowsight, and run `data/load_data.sql`.

- Setup uses `IF NOT EXISTS`; it does not replace tables or load records.
- Loading uses explicit filenames, a CSV format, and `ON_ERROR = 'ABORT_STATEMENT'`.
- COPY normally skips unchanged files already loaded. Do not add `FORCE=TRUE` to retry a partially completed load.
- Expected final counts are 500 patients, 5,000 encounters, and 1,500 notes.

### Recovery only

`data/fallback_data.sql` is an alternative when uploads remain blocked or lab counts need resetting. Ask the facilitator first.

**It replaces all rows in all three lab tables.** Run setup first. The recovery script loads the exact CSV values in a transaction with an exception handler that rolls back on failure. It is not for production or customized tables. After recovery, verify counts and continue with the exercises; do not combine it with another CSV load.

## Facilitator checklist

Before the session:

- Provide individual trial accounts, access details, and the three-day post-lab expiration information.
- Verify login, `SYSADMIN` access, and the ability to create the lab warehouse, database, stage, tables, and warehouse-runtime Streamlit app. The optional access exercise also needs `USERADMIN`.
- Confirm CoCo access and its account prerequisites using the [official CoCo documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight). Do not assume every trial is AI-enabled. If unavailable, demonstrate it while participants continue with the supplied code.
- Walk through private `snowcamp` workspace creation and stage uploads in the current Snowsight UI.
- Run the full participant flow, including the Streamlit app, recovery path, and optional permission-denial tests in an isolated demo environment.

During the session:

- Explain the distinction between the Snowsight user-menu role, SQL-file role, and CoCo session role.
- Check row counts before proceeding to SQL analysis.
- Run intentional-error examples one statement at a time, especially DROP/UNDROP and access tests.
- Keep the app private unless its displayed data is approved for the intended viewers. The warehouse-runtime app uses owner rights; direct table grants do not determine everything a viewer can see through it.
- Prioritize core checkpoints over optional exercises when time is limited.

## Relationship to the Cortex AI Lab

This is a **skills prerequisite**, not a shared-data continuation, of the [Value-Based Care Cortex AI Lab](https://github.com/sfc-gh-mwalli/Cortex-AI-Lab).

Day 0 uses `DAY0_LAB.HEALTHCARE` and three simplified teaching tables. The AI lab uses its own setup, `VBC_LAB.CARE_ANALYTICS`, the `SYNTHEA.SILVER` dataset, additional tables, different column names, and separate clinical-note assets. Follow that lab's setup and downloads; do not substitute the Day 0 CSVs or skip its data acquisition steps. That course includes Marketplace setup; this course does not.

## Repository layout

```text
index.html                    Single-page lab guide
assets/app.js                 Step navigation, optional-module ordering, copy buttons
assets/styles.css             Responsive light/dark styling
data/patients.csv             Fictional patient data
data/encounters.csv           Fictional encounter data
data/clinical_notes.csv       Fictional clinical notes
data/setup.sql                Infrastructure only
data/load_data.sql            Load staged CSVs and check counts
data/fallback_data.sql        Generated exact-data recovery script
data/generate_data.py         Deterministic CSV generator (seed 42)
streamlit/streamlit_app.py     Completed warehouse-runtime app
build_materials.py            Generate recovery SQL and download ZIP
verify_materials.py           Local consistency checks
snowcamp-materials.zip        Participant download bundle
.github/workflows/pages.yml   GitHub Pages deployment on pushes to main
```

## Maintain and preview the site

Run these commands from the repository root. Python 3 is required for building/checking materials; Node.js is used only for the JavaScript syntax check.

```bash
python3 build_materials.py
python3 verify_materials.py
node --check assets/app.js
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/`. Check navigation, downloads, copy buttons, and the **Try it with CoCo** panels at desktop and narrow screen widths.

- Edit the guide in `index.html`. Keep its Python examples consistent with `streamlit/streamlit_app.py`.
- Only run `python3 data/generate_data.py` when intentionally regenerating the source CSVs.
- After changing guide files, app code, or data, rerun `build_materials.py` and `verify_materials.py`. The deployment workflow does **not** rebuild the ZIP for you.
- Commit only intended source files and regenerated artifacts. Push to `main` to deploy through GitHub Actions, then verify the live site.
- Keep credentials, personal account data, and local tooling state out of this public repository.

## Validation scope

Local checks cover module timing, one CoCo practice panel per module, local links, Python syntax, parity between embedded and downloadable app code, CSV relationships, recovery values, and ZIP contents. Browser checks have covered section navigation and narrow-width overflow. Selected earlier SQL examples were exercised in a demo account.

These checks do **not** establish that the complete revised lab has passed a participant-style Snowsight walkthrough. Deployed Streamlit behavior, isolated-role denial tests, and recovery transaction failure behavior still require verification in an authorized demo account. No new trial account is required for that verification.
