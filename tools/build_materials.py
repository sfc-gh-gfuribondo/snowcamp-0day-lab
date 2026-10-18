"""Build both guides, recovery SQL, and the two download ZIPs locally."""
import csv
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from build_guide import build_guide

ROOT = Path(__file__).resolve().parent.parent


def sql_value(value):
    return "'" + value.replace("'", "''") + "'"


def main():
    build_guide()
    lines = [
        "-- RECOVERY ONLY: replaces ALL rows in the three DAY0_LAB lab tables.",
        "-- Run setup.sql first. Do NOT run against production or customized tables.",
        "-- This uses the EXACT downloaded CSV values, not new random data.",
        "-- Run the entire file. The anonymous SQL block rolls back all three",
        "-- replacements if a load fails. Review the error before retrying.",
        "-- Do not upload/load CSVs afterwards: this is an alternative loading path.",
        "-- Runs as ACCOUNTADMIN: the line below fixes the file's role, which can default to SYSADMIN.",
        "USE ROLE ACCOUNTADMIN;",
        "USE WAREHOUSE LAB_WH;",
        "USE SCHEMA DAY0_LAB.HEALTHCARE;",
        "EXECUTE IMMEDIATE $$",
        "BEGIN",
        "BEGIN TRANSACTION;",
    ]
    for name in ("patients", "encounters", "clinical_notes"):
        with (ROOT / "data" / f"{name}.csv").open(newline="") as handle:
            records = list(csv.reader(handle))
        columns, rows = records[0], records[1:]
        lines.append(f"INSERT OVERWRITE INTO {name.upper()} ({', '.join(columns)}) VALUES")
        lines.append(",\n".join("(" + ",".join(sql_value(value) for value in row) + ")" for row in rows) + ";")
    lines.extend([
        "COMMIT;",
        "EXCEPTION",
        "  WHEN OTHER THEN",
        "    ROLLBACK;",
        "    RAISE;",
        "END;",
        "$$;",
        "SELECT 'PATIENTS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM PATIENTS",
        "UNION ALL SELECT 'ENCOUNTERS', COUNT(*) FROM ENCOUNTERS",
        "UNION ALL SELECT 'CLINICAL_NOTES', COUNT(*) FROM CLINICAL_NOTES;",
    ])
    (ROOT / "data" / "fallback_data.sql").write_text("\n".join(lines) + "\n")
    files = ["index.html", "assets/app.js", "assets/styles.css", "streamlit/streamlit_app.py",
             "explore.sql", "time_travel.ipynb", "guide.html", "assets/guide.css", "assets/guide.js"]
    files += [f"data/{name}" for name in (
        "patients.csv", "encounters.csv", "clinical_notes.csv", "payer_budget.csv", "setup.sql", "load_data.sql", "fallback_data.sql", "teardown.sql"
    )]
    with ZipFile(ROOT / "snowcamp-data.zip", "w", compression=ZIP_DEFLATED) as archive:
        for name in ("patients.csv", "encounters.csv", "clinical_notes.csv"):
            archive.write(ROOT / "data" / name, name)
    files.append("snowcamp-data.zip")
    with ZipFile(ROOT / "snowcamp-materials.zip", "w", compression=ZIP_DEFLATED) as archive:
        for relative in files:
            archive.write(ROOT / relative, relative)
    print(f"Built alternate guide, recovery SQL, data-only ZIP (3 CSVs), and fallback bundle ({len(files)} files).")


if __name__ == "__main__":
    main()
