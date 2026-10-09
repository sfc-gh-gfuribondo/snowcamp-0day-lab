# Day 0 Lab - My First Streamlit App
# Paste this into a new Streamlit app in Snowsight (Projects > Streamlit).
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.title("Encounter Explorer")
st.caption("Built on DAY0_LAB.HEALTHCARE.ENCOUNTER_SUMMARY")

session = get_active_session()  # already logged in - no password needed

# Load the view you created in Module 4 into a pandas DataFrame.
df = session.table("DAY0_LAB.HEALTHCARE.ENCOUNTER_SUMMARY").to_pandas()

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
st.dataframe(df.sort_values("TOTAL_COST", ascending=False).head(20), use_container_width=True)

# Module 6, step 4: clinical notes search (parameterized - never paste user input into SQL)
st.subheader("Search clinical notes")
term = st.text_input("Find notes containing", "shortness of breath")
if term:
    notes = session.sql(
        """SELECT NOTE_DATE, PATIENT_ID, NOTE_TEXT
           FROM DAY0_LAB.HEALTHCARE.CLINICAL_NOTES
           WHERE NOTE_TEXT ILIKE ?
           ORDER BY NOTE_DATE DESC
           LIMIT 50""",
        params=[f"%{term}%"],
    ).to_pandas()
    st.write(f"{len(notes)} notes found (showing up to 50)")
    st.dataframe(notes, use_container_width=True)
