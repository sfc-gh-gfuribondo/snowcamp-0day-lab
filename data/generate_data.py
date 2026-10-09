"""Generate the small synthetic healthcare CSVs used by the Day 0 lab.

Deterministic (fixed seed) so every run produces identical files.
All people, places-to-person mappings, and notes are fictional.

    python3 data/generate_data.py
"""
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 42
N_PATIENTS = 500
N_ENCOUNTERS = 5000
N_NOTES = 1500
OUT = Path(__file__).parent

FIRST_F = ["Maria", "Linda", "Susan", "Aisha", "Mei", "Olivia", "Grace", "Rosa", "Hannah", "Priya",
           "Emma", "Nora", "Elena", "Fatima", "Chloe", "Ava", "Sofia", "Leah", "Ruth", "Ivy"]
FIRST_M = ["James", "Robert", "Carlos", "Wei", "Daniel", "Omar", "Liam", "Noah", "Ethan", "Raj",
           "Lucas", "Mateo", "Samuel", "Henry", "Jamal", "Leo", "Owen", "Isaac", "Victor", "Hugo"]
LAST = ["Smith", "Johnson", "Garcia", "Nguyen", "Brown", "Patel", "Kim", "Lopez", "Walker", "Chen",
        "Murphy", "Rivera", "Okafor", "Silva", "Cohen", "Reyes", "Hughes", "Price", "Ward", "Ross"]
CITIES = [("Boston", "Suffolk"), ("Worcester", "Worcester"), ("Springfield", "Hampden"),
          ("Cambridge", "Middlesex"), ("Lowell", "Middlesex"), ("Brockton", "Plymouth"),
          ("Quincy", "Norfolk"), ("Lynn", "Essex"), ("New Bedford", "Bristol"), ("Pittsfield", "Berkshire")]
RACES = ["white", "black", "asian", "hispanic", "other"]
RACE_W = [55, 15, 12, 14, 4]
PAYERS = ["Medicare", "Medicaid", "Blue Cross", "Aetna", "UnitedHealthcare", "No Insurance"]
PAYER_W = [25, 18, 22, 13, 15, 7]

# encounter class -> (weight, descriptions, cost range)
CLASSES = {
    "wellness":   (30, ["Annual wellness visit", "Well child visit"], (90, 250)),
    "ambulatory": (30, ["Follow-up visit", "Chronic disease check", "Medication review"], (120, 400)),
    "outpatient": (15, ["Outpatient procedure", "Imaging study", "Physical therapy"], (300, 2500)),
    "urgentcare": (10, ["Urgent care visit"], (150, 600)),
    "emergency":  (10, ["Emergency room admission", "ED visit for chest pain"], (900, 6000)),
    "inpatient":  (5,  ["Hospital admission", "Admission for pneumonia"], (6000, 40000)),
}
CONDITIONS = ["type 2 diabetes", "hypertension", "asthma", "COPD", "heart failure",
              "chronic kidney disease", "depression", "hyperlipidemia", "osteoarthritis", "obesity"]


def rand_date(rng, start, end):
    return start + timedelta(days=rng.randrange((end - start).days))


def main():
    rng = random.Random(SEED)

    patients = []
    for i in range(1, N_PATIENTS + 1):
        gender = rng.choice(["F", "M"])
        city, county = rng.choice(CITIES)
        patients.append({
            "PATIENT_ID": f"P{i:04d}",
            "FIRST_NAME": rng.choice(FIRST_F if gender == "F" else FIRST_M),
            "LAST_NAME": rng.choice(LAST),
            "BIRTHDATE": rand_date(rng, date(1935, 1, 1), date(2018, 12, 31)).isoformat(),
            "GENDER": gender,
            "RACE": rng.choices(RACES, RACE_W)[0],
            "CITY": city,
            "COUNTY": county,
            "STATE": "MA",
            "INCOME": rng.randrange(15, 200) * 1000,
            "PAYER": rng.choices(PAYERS, PAYER_W)[0],
            "PRIMARY_CONDITION": rng.choice(CONDITIONS + ["none"] * 3),
        })

    names = list(CLASSES)
    weights = [CLASSES[c][0] for c in names]
    encounters = []
    for i in range(1, N_ENCOUNTERS + 1):
        p = rng.choice(patients)
        cls = rng.choices(names, weights)[0]
        _, descs, (lo, hi) = CLASSES[cls]
        start = datetime.combine(rand_date(rng, date(2023, 1, 1), date(2025, 12, 31)),
                                 datetime.min.time()) + timedelta(minutes=rng.randrange(7 * 60, 20 * 60))
        hours = rng.randrange(48, 240) if cls == "inpatient" else rng.randrange(1, 6)
        total = round(rng.uniform(lo, hi), 2)
        encounters.append({
            "ENCOUNTER_ID": f"E{i:05d}",
            "PATIENT_ID": p["PATIENT_ID"],
            "START_TS": start.strftime("%Y-%m-%d %H:%M:%S"),
            "STOP_TS": (start + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S"),
            "ENCOUNTER_CLASS": cls,
            "DESCRIPTION": rng.choice(descs),
            "TOTAL_COST": total,
            "PAYER_COVERAGE": 0 if p["PAYER"] == "No Insurance" else round(total * rng.uniform(0.5, 0.9), 2),
        })

    by_id = {p["PATIENT_ID"]: p for p in patients}
    notes = []
    for i, e in enumerate(rng.sample(encounters, N_NOTES), start=1):
        p = by_id[e["PATIENT_ID"]]
        cond = p["PRIMARY_CONDITION"]
        hx = "no significant chronic conditions" if cond == "none" else f"a history of {cond}"
        plan = rng.choice(["Continue current medications.", "Adjust medication dose and recheck in 4 weeks.",
                           "Refer to specialist.", "Order labs and follow up in 2 weeks.",
                           "Reinforce diet and exercise counseling."])
        notes.append({
            "NOTE_ID": f"N{i:05d}",
            "PATIENT_ID": p["PATIENT_ID"],
            "ENCOUNTER_ID": e["ENCOUNTER_ID"],
            "NOTE_DATE": e["START_TS"][:10],
            "NOTE_TYPE": "SOAP",
            "NOTE_TEXT": (f"S: Patient seen for {e['DESCRIPTION'].lower()}. Reports "
                          f"{rng.choice(['feeling well', 'mild fatigue', 'intermittent pain', 'shortness of breath', 'poor sleep'])}. "
                          f"O: BP {rng.randrange(105, 165)}/{rng.randrange(65, 100)}, HR {rng.randrange(58, 105)}. "
                          f"A: Patient with {hx}. "
                          f"P: {plan}"),
        })

    for name, rows in [("patients", patients), ("encounters", encounters), ("clinical_notes", notes)]:
        with open(OUT / f"{name}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"{name}.csv: {len(rows)} rows")


if __name__ == "__main__":
    main()
