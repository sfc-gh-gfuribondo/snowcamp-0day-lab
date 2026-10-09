"""Build exact-data SQL recovery and the downloadable workshop bundle locally."""
import csv
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent


def sql_value(value):
    return "'" + value.replace("'", "''") + "'"


def main():
    lines = [
        "-- RECOVERY ONLY: replaces ALL rows in the three DAY0_LAB lab tables.",
        "-- Run setup.sql first. Do NOT run against production or customized tables.",
        "-- This uses the EXACT downloaded CSV values, not new random data.",
        "-- Run the entire file. The anonymous SQL block rolls back all three",
        "-- replacements if a load fails. Review the error before retrying.",
        "-- Do not upload/load CSVs afterwards: this is an alternative loading path.",
        "USE ROLE SYSADMIN;",
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
    files = ["index.html", "assets/app.js", "assets/styles.css", "streamlit/streamlit_app.py"]
    files += [f"data/{name}" for name in (
        "patients.csv", "encounters.csv", "clinical_notes.csv", "setup.sql", "load_data.sql", "fallback_data.sql"
    )]
    with ZipFile(ROOT / "snowcamp-materials.zip", "w", compression=ZIP_DEFLATED) as archive:
        for relative in files:
            archive.write(ROOT / relative, relative)
    print(f"Built exact-data recovery SQL and bundle ({len(files)} files).")


if __name__ == "__main__":
    main()
