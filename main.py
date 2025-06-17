import streamlit as st

st.title("Sporttest-App")

tabs = st.tabs(["Personen", "Tests", "FTP-Test", "Trainingsplan"])
with tabs[0]:
    st.header("Personendaten")
    st.write("Name:")
    st.write("Geburtstag:")
    st.write("Adresse:")

with tabs[1]:
    st.header("Ruhe-EKG")


    st.header("Lungentest")

with tabs[2]:
    st.header("Stufentest Fahrradergometer")
    st.write("Zusammenfassung")
    st.write("Datum")
    st.write("Gesamtdauer")


with tabs[3]:
    st.header("Trainingsplan erstellen:")
    st.write("HIER TABELLE EINBAUEN")