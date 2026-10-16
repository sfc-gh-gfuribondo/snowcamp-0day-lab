# Day 0 Lab - My First Streamlit App
# Reference: paste into the app created with Workspaces > + Add new > Streamlit app.
import streamlit as st

st.title("Encounter Explorer")
st.caption("Synthetic teaching data | DAY0_LAB.HEALTHCARE.ENCOUNTER_SUMMARY")

conn = st.connection("snowflake")  # Snowflake supplies the credentials

# Cache the view for 60 seconds, then apply sidebar filters locally.
df = conn.query("SELECT * FROM DAY0_LAB.HEALTHCARE.ENCOUNTER_SUMMARY", ttl=60)

# Sidebar filters
cities = st.sidebar.multiselect("City", sorted(df["CITY"].unique()))
payers = st.sidebar.multiselect("Payer", sorted(df["PAYER"].unique()))
if cities:
    df = df[df["CITY"].isin(cities)]
if payers:
    df = df[df["PAYER"].isin(payers)]

# Headline numbers
c1, c2, c3 = st.columns(3)
c1.metric("Encounters", f"{len(df):,}")
c2.metric("Patients", f"{df['PATIENT_ID'].nunique():,}")
c3.metric("Total cost", f"${df['TOTAL_COST'].sum():,.0f}")

st.subheader("Total cost by encounter class")
st.bar_chart(df.groupby("ENCOUNTER_CLASS")["TOTAL_COST"].sum())

st.subheader("Most expensive encounters")
st.dataframe(df.sort_values("TOTAL_COST", ascending=False).head(20), width="stretch")

# Clinical notes search is separate from the encounter filters above.
st.subheader("Search clinical notes")
term = st.text_input("Find notes containing", "shortness of breath")
if term:
    notes = conn.query(
        """SELECT NOTE_DATE, PATIENT_ID, NOTE_TEXT
           FROM DAY0_LAB.HEALTHCARE.CLINICAL_NOTES
           WHERE NOTE_TEXT ILIKE ?
           ORDER BY NOTE_DATE DESC
           LIMIT 50""",
        params=[f"%{term}%"],
        ttl=60,
    )
    st.write(f"Showing {len(notes)} matching notes (maximum 50; not a total count)")
    st.dataframe(notes, width="stretch")
