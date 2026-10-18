# Snowflake Foundations: Day 0 Lab

A hands-on introduction for people brand new to Snowflake, with an estimated 82 minutes of core exercises. Allow **105-120 minutes** for a facilitated beginner session, including questions, startup waits, and troubleshooting. Start with a guided Snowsight tour, create a private Git-connected workspace, load fictional healthcare data, query it with SQL, recover an accidental change with Time Travel, and build a Streamlit app.

**[Open the lab guide](https://sfc-gh-gfuribondo.github.io/snowcamp-0day-lab/)** · **[Download lab data](https://sfc-gh-gfuribondo.github.io/snowcamp-0day-lab/snowcamp-data.zip)**

No Marketplace installation or local development tools are required for participants.

## Your lab account

Each participant receives a **personal Snowflake trial account** from the facilitator. It remains active for **three days after the lab** so you can revisit exercises and continue practicing.

- Use the supplied account URL and sign-in instructions. Do not create another trial or use a production account.
- Select `ACCOUNTADMIN` once at the start and keep it for every module, including optional exercises. This is an isolated-workshop shortcut, not a production practice; use least-privilege roles in production.
- Confirm the exact expiration time with your facilitator.
- Download your edited SQL, notebook, and Python files, including your final app code, before access expires. Notebook outputs are not stored in the `.ipynb` file; export results as HTML separately if wanted. Keep the original data ZIP locally. Public-repository authentication does not let you push edits back to the lab repository.

## Start here

1. Open the [lab guide](https://sfc-gh-gfuribondo.github.io/snowcamp-0day-lab/) and sign in to your provided account in another browser tab.
2. Download and unzip `snowcamp-data.zip`: it contains only the three CSVs, with no subfolders.
3. Follow the guide to create `SNOWCAMP_GIT_INTEGRATION` in a bootstrap SQL file in My Workspace, using `ACCOUNTADMIN` in the provided lab account. Set the Snowsight user-menu role to `ACCOUNTADMIN` before opening the Git dialog; its role is separate from the SQL-file role.
4. Choose **From Git repository**, enter `https://github.com/sfc-gh-gfuribondo/snowcamp-0day-lab.git`, select the integration and **Public repository** authentication, and name the workspace `snowcamp`. No GitHub login, token, or fork is needed. Find the supplied `explore.sql` and `time_travel.ipynb` at the root; do not create blank files. Leave `ACCOUNTADMIN` selected.
5. Run `data/setup.sql` to create the lab infrastructure, including `LAB_STREAMLIT_POOL`. Setup makes it the account's default Streamlit pool and sets your user's default warehouse to `LAB_WH`; these settings are for your isolated workshop account only. Upload the three extracted CSVs (not the ZIP) to the root of `DAY0_LAB.HEALTHCARE.LAB_DATA`, leaving the optional path blank, then run `data/load_data.sql`.
6. Open prepopulated `explore.sql` for SQL Basics. Run section 0 for context, then sections 1-6 separately; section 6 creates the app's view. Open `time_travel.ipynb` for Time Travel, connect notebook compute, and run one cell at a time, **never Run all**. After restoring both tables, suspend the notebook service.
7. In `snowcamp`, select **+ Add new > Streamlit app**, use its generated app folder and configuration, select `LAB_WH` as the query warehouse, and paste the lab Python into the generated `streamlit_app.py`. **Run** gives a private preview; **Deploy** is optional and creates a separate Streamlit object in `DAY0_LAB.HEALTHCARE`. Keep `ACCOUNTADMIN` selected.

**Git supplies code to the workspace. Extracted CSVs go onto the database stage. COPY loads rows into tables.** CSVs visible in the Git workspace are not automatically staged or loaded.

If Git setup is blocked, ask the facilitator and use the [full materials bundle](https://sfc-gh-gfuribondo.github.io/snowcamp-0day-lab/snowcamp-materials.zip) as a fallback. Create a private `snowcamp` workspace and upload the SQL, notebook, and Python files manually; those files may be at the workspace root rather than the paths shown above. The full bundle includes `explore.sql` and `time_travel.ipynb`; the data-only ZIP still contains exactly three CSVs.

## Agenda

| Core section | Minutes |
| --- | ---: |
| Lab overview | 3 |
| Snowsight tour and workspace creation | 12 |
| Meet CoCo | 6 |
| Set up and load data | 18 |
| SQL basics | 15 |
| Time Travel | 10 |
| Your first Streamlit app | 15 |
| Wrap-up and next steps | 3 |
| **Total** | **82** |

Optional extensions follow the core wrap-up: **SQL Challenges** (8 minutes) and **Roles and Access** (10 minutes).

Every module except Lab Overview includes an always-visible **Try it with CoCo** practice section with a CoCo mascot heading, copyable prompts, and a success check. These activities are additional practice, outside the 82-minute core timing.
The Meet CoCo practice works before data loading: map the workspace, explain setup without running it, or solve a three-visit healthcare puzzle using inline values.

**For a 90-minute session:** follow the core modules through Wrap-Up, including the Meet CoCo introduction. Save extra CoCo practice, SQL Challenges, Roles and Access, the bonus clone, and app deployment for later. Defer the Query Profile tour if behind. Preserve the row-count checks, creation of `DAY0_LAB.HEALTHCARE.ENCOUNTER_SUMMARY`, table restoration, app preview, and compute suspension. Completing all optional activities needs additional time beyond the recommended beginner session.

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
- Setup creates `LAB_STREAMLIT_POOL` with `CPU_X64_XS`, `MIN_NODES = 1`, `MAX_NODES = 2`, automatic resume, and initial suspension. Two nodes allow the private preview and optional deployed app to coexist. It sets `DEFAULT_STREAMLIT_COMPUTE_POOL` at account level and the signed-in user's `DEFAULT_WAREHOUSE`; reruns reapply these defaults, but do not alter an existing pool's sizing.
- The pool's `AUTO_SUSPEND_SECS = 60` applies only when no services or jobs are active. A running Streamlit app keeps the pool active even without queries. At wrap-up, close app tabs and suspend the dedicated lab pool separately from `LAB_WH`.
- Loading uses explicit filenames, a CSV format, and `ON_ERROR = 'ABORT_STATEMENT'`.
- COPY normally skips unchanged files already loaded. Do not add `FORCE=TRUE` to retry a partially completed load.
- Expected final counts are 500 patients, 5,000 encounters, and 1,500 notes.

### Additional practice: let CoCo load a payer budget

After verifying the three core tables, the Load Data module's **Try it with CoCo** section uses `data/payer_budget.csv` from the workspace to propose and, after approval, load a separate `DAY0_LAB.HEALTHCARE.PAYER_BUDGET` table. Start a new chat because the earlier read-only restriction cannot be relaxed in that chat. Keep `ACCOUNTADMIN` selected and retain write approvals. If the table exists, stop rather than overwrite it or append duplicates.

The file contains 12 fictional month/plan records for January-April 2026, with budgeted claims in USD and member-month counts. One row represents one month and plan type; the figures are illustrative, not benchmarks or actuals linked to the encounter dataset. Check 12 rows, unique `(BUDGET_MONTH, PLAN_TYPE)` pairs, and total budgeted claims of **$1,980,000.00**. Only the full materials bundle includes this extra CSV; the data-only ZIP still contains exactly the original three files.

Rehearse workspace-file access and loading with CoCo in the provided demo account before delivery. This is additional practice outside core timing; skip it if tools or permissions prevent the load. Do not add credentials or substitute invented rows. No downstream lab exercise depends on this table, and `fallback_data.sql` does not reset it.

### Recovery only

`data/fallback_data.sql` is an alternative when uploads remain blocked or lab counts need resetting. Ask the facilitator first.

**It replaces all rows in all three lab tables.** Run setup first. The recovery script loads the exact CSV values in a transaction with an exception handler that rolls back on failure. It is not for production or customized tables. After recovery, verify counts and continue with the exercises; do not combine it with another CSV load.

## Facilitator checklist

Before the session:

- Provide individual trial accounts, access details, and the three-day post-lab expiration information.
- Verify login and `ACCOUNTADMIN` access for all lab objects and the Streamlit app. Configure the student's default role as `ACCOUNTADMIN` in the isolated workshop account before the session and verify new SQL files and CoCo start with that role. A user-menu selection is not a global role change across existing sessions.
- Confirm CoCo access and its account prerequisites using the [official CoCo documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight). Do not assume every trial is AI-enabled. If unavailable, demonstrate it while participants continue with the supplied code.
- Verify the `ACCOUNTADMIN` Git bootstrap works and the integration allows the lab repository URL. Subsequent scripts must not change roles.
- Walk through public Git-connected `snowcamp` workspace creation and data-only ZIP extraction/stage uploads in the current Snowsight UI. Keep the full materials bundle available as a fallback.
- Verify workspace Streamlit support, `CPU_X64_XS` availability/capacity, and that STREAMLIT workloads are allowed in the provided accounts. Setup now creates `LAB_STREAMLIT_POOL`, configures it as the default pool, and sets the signed-in user's default warehouse to `LAB_WH`; no pool needs to be precreated. Confirm those setup results and rehearse first app startup. Workspace apps use container runtime: compute-pool usage is separate from warehouse billing, and workspace nodes are released after three hours of inactivity. See the [workspace prerequisites](https://docs.snowflake.com/en/developer-guide/streamlit/streamlit-in-workspaces/streamlit-in-workspaces-overview).
- Verify workspace notebook access, a suitable CPU notebook service/pool, permission for NOTEBOOK workloads, and `LAB_WH` as the notebook query warehouse. Use a short notebook-service idle timeout (15 minutes if offered). Do not assume the Streamlit pool is the notebook pool; verify notebook runtime capacity and suspend the notebook service after restoration, before starting Streamlit. See [notebook compute setup](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-in-workspaces/notebooks-in-workspaces-compute-setup).
- Run the full participant flow, including workspace preview, optional deployment, recovery, and optional grant inspection in an isolated demo environment.
- Before delivery, verify the generated Streamlit starter runs with the supplied account's package/network restrictions, the completed app filters and notes search work, and the Time Travel notebook preserves the saved SQL timestamp across cells and recovers both tables on a first run and a repeat. Rehearse running UNDROP directly after the intentional error. Local consistency checks do not replace this rehearsal.

During the session:

- Explain the distinction between the Snowsight user-menu role, SQL-file role, and CoCo session role. All should remain `ACCOUNTADMIN`; correct any mismatched initial configuration before continuing.
- Check row counts before proceeding to SQL analysis.
- Run `explore.sql` one numbered section at a time and `time_travel.ipynb` one cell at a time. Never use Run all on the recovery notebook; run UNDROP directly after the expected missing-table error. Skip recovery-only cells on the normal path. The optional access exercise inspects grants; it does not switch to `CARE_TEAM` or claim to prove permission denials while running as `ACCOUNTADMIN`.
- Keep `PATIENTS_BEFORE_EXERCISE` as the fixed safety-clone name. If it already exists, stop before the intentional update; do not rename or replace it. Verify its original lab contents, restore and check the saved city counts, then repeat from `SET before_mistake` without recreating the clone. If its contents cannot be verified, use the facilitator-led exact-data recovery path instead.
- Keep the workspace preview private. If deploying, review the target location, compute pool, query warehouse, and sharing grants. The deployed app uses the default owner's-rights connection; direct table grants do not determine everything a viewer can see through it.
- Prioritize core checkpoints over optional exercises when time is limited.
- After Time Travel restoration, suspend the notebook service from the Connected menu; closing its tab does not stop it. At wrap-up, close app tabs and suspend `LAB_STREAMLIT_POOL` as well as any running `LAB_WH`. Suspending this dedicated lab pool pauses its apps; reopening an app can auto-resume it.

## Relationship to the Cortex AI Lab

This is a **skills prerequisite**, not a shared-data continuation, of the [Value-Based Care Cortex AI Lab](https://github.com/sfc-gh-mwalli/Cortex-AI-Lab).

Day 0 uses `DAY0_LAB.HEALTHCARE` and three simplified teaching tables. The AI lab uses its own setup, `VBC_LAB.CARE_ANALYTICS`, the `SYNTHEA.SILVER` dataset, additional tables, different column names, and separate clinical-note assets. Follow that lab's setup and downloads; do not substitute the Day 0 CSVs or skip its data acquisition steps. That course includes Marketplace setup; this course does not.

## Repository layout

```text
index.html                    Single-page lab guide
guide.html                    Generated continuous developer-style edition
build_guide.py                Reuse canonical modules in the alternate layout
assets/guide-template.html    Alternate shell; keep lesson edits in index.html
assets/guide.css              Isolated alternate design and responsive layout
assets/guide.js               Contents navigation, active section, copy controls
test_build_guide.py           Offline alternate generator regression tests
explore.sql                   Prepopulated numbered SQL Basics exercises
time_travel.ipynb              Step-by-step SQL-cell workspace recovery notebook
assets/app.js                 Step navigation, optional-module ordering, copy buttons
assets/styles.css             Responsive light/dark styling
data/patients.csv             Fictional patient data
data/encounters.csv           Fictional encounter data
data/clinical_notes.csv       Fictional clinical notes
data/payer_budget.csv         12 fictional records for the extra CoCo loading exercise
data/setup.sql                Infrastructure only
data/load_data.sql            Load staged CSVs and check counts
data/fallback_data.sql        Generated exact-data recovery script
data/generate_data.py         Deterministic CSV generator (seed 42)
streamlit/streamlit_app.py     Container-runtime reference app for workspace exercise
build_materials.py            Generate alternate guide, recovery SQL, and both ZIPs
verify_materials.py           Local consistency checks
snowcamp-data.zip             Primary download: exactly three CSVs at ZIP root
snowcamp-materials.zip        Fallback bundle: guide, code, CSVs, and data ZIP
.github/workflows/pages.yml   GitHub Pages deployment on pushes to main
```

## Maintain and preview the site

Run these commands from the repository root. Python 3 is required for building/checking materials; Node.js is used only for the JavaScript syntax check.

```bash
python3 build_materials.py
python3 verify_materials.py
python3 test_build_guide.py
node --check assets/app.js
node --check assets/guide.js
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/`. Check navigation, downloads, copy buttons, and the **Try it with CoCo** panels at desktop and narrow screen widths.

### Alternate developer-guide edition

Preview `http://127.0.0.1:8765/guide.html` for a continuous-reading version inspired by the [Snowflake developer guide layout](https://www.snowflake.com/en/developers/guides/ai-powered-video-publishing/): charcoal hero, large headings, a right-hand contents sidebar, and the same CoCo logos and visible practice sections. It does not replace the original step-by-step guide.

`guide.html` is generated from `index.html` at build time, not fetched at runtime. All lesson text, SQL, prompts, links, and logos stay synchronized; only headings and presentation change. Optional extensions follow core wrap-up. Edit the layout in `assets/guide-template.html`, `assets/guide.css`, and `assets/guide.js`; do not hand-edit generated `guide.html`. No third-party scripts, fonts, trackers, or runtime network calls are used. Both guides remain readable from the full 17-file materials ZIP.

The alternate supports native section links, keyboard focus, a compact mobile contents menu, clipboard-failure selection, and reduced motion. With JavaScript disabled, all instructions and navigation remain visible; copy text manually. Check both editions before publishing. Building locally does not commit, push, or change the live site.

### Content maintenance

- Edit the guide in `index.html`. Keep its SQL Basics examples consistent with `explore.sql`, notebook directions consistent with `time_travel.ipynb`, and Python examples consistent with `streamlit/streamlit_app.py`.
- Only run `python3 data/generate_data.py` when intentionally regenerating the source CSVs.
- After changing guide files, app code, or data, rerun `build_materials.py` and `verify_materials.py`. The deployment workflow does **not** rebuild the ZIPs for you.
- Commit only intended source files and regenerated artifacts. Push to `main` to deploy through GitHub Actions, then verify the live site.
- Keep credentials, personal account data, and local tooling state out of this public repository.

## Validation scope

Local checks cover parity between both guides (all modules, text, code, prompts, links, CoCo logos, and heading hierarchy), generator regression tests, module timing, nine CoCo practice panels (one per module except Lab Overview), immediate Meet CoCo prompts, local links, Python syntax, parity between embedded and downloadable setup/exploration SQL and app code, notebook structure and recovery-cell order, compute-pool configuration and cleanup instructions, CSV relationships, recovery values, and ZIP contents. Browser checks have covered section navigation and narrow-width overflow. Selected earlier SQL examples were exercised in a demo account.

These checks do **not** establish that the complete revised lab has passed a participant-style Snowsight walkthrough. The new notebook and compute-pool/default-warehouse SQL have not been executed against Snowflake. CoCo workspace-CSV ingestion, notebook SQL session continuity, expected-error recovery, pool provisioning, workspace preview, deployed Streamlit behavior, new-session/default-role consistency, and recovery transaction failure behavior still require verification in an authorized demo account. No new trial account is required for that verification.
