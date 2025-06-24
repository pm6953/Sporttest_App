import streamlit as st
from read_ekgdata import EKGdata
from read_persondata import Person
import json
from PIL import Image

st.title("Sporttest-App")

tabs = st.tabs(["Personen", "Tests", "FTP-Test", "Trainingsplan"])
with tabs[0]:
    st.header("Personendaten")

    persons_list = Person.load_person_data()
    person_names = Person.get_person_list(persons_list)

    # Spalten für Selectbox und Plus-Button nebeneinander
    col1, col2 = st.columns([9, 1])

    with col1:
        selected_person_name = st.selectbox('Versuchsperson', options=person_names, key="sbVersuchsperson")

    with col2:
        # Vertikal zentrieren mit padding oben (ca. 15px, je nach optischer Feinjustierung)
        st.markdown("""
            <style>
            div.stButton > button:first-child {
                margin-top: 20px;
                height: 35px;
                width: 35px;
                font-size: 22px;
            }
            </style>
            """, unsafe_allow_html=True)
        add_new = st.button("➕", help="Neue Person hinzufügen")

    # Formular anzeigen, wenn Plus geklickt oder im Session State gesetzt
    if add_new:
        st.session_state['show_new_person_form'] = True

    if st.session_state.get('show_new_person_form', False):
        st.subheader("➕ Neue Person anlegen")

        with st.form("neue_person_formular"):
            firstname = st.text_input("Vorname")
            lastname = st.text_input("Nachname")
            birth_year = st.number_input("Geburtsjahr", min_value=1900, max_value=2025, value=2000)
            gender = st.selectbox("Geschlecht", options=["male", "female"])
            address = st.text_input("Adresse")
            picture_path = st.text_input("Bildpfad (optional)", value="data/pictures/none.jpg")

            submitted = st.form_submit_button("Person hinzufügen")

            if submitted:
                persons_list = Person.load_person_data()
                exists = any(p["firstname"] == firstname and p["lastname"] == lastname for p in persons_list)

                if exists:
                    st.warning("Diese Person existiert bereits.")
                else:
                    new_id = max([int(p["id"]) for p in persons_list] + [0]) + 1

                    neue_person = {
                        "id": new_id,
                        "firstname": firstname,
                        "lastname": lastname,
                        "date_of_birth": birth_year,
                        "gender": gender,
                        "address": address,
                        "picture_path": picture_path
                    }

                    persons_list.append(neue_person)

                    with open("data/person_db.json", "w", encoding="utf-8") as f:
                        json.dump(persons_list, f, ensure_ascii=False, indent=4)

                    st.success(f"{firstname} {lastname} wurde hinzugefügt.")
                    st.session_state['show_new_person_form'] = False
                    st.experimental_rerun()

    # Jetzt unten: Bild und Daten nebeneinander anzeigen
    person_data = Person.find_person_data_by_name(selected_person_name)
    if person_data:
        person = Person(person_data)

        if "picture_path" in person_data:
            st.session_state.picture_path = person_data["picture_path"]
        else:
            st.session_state.picture_path = 'data/pictures/none.jpg'

        col1_data, col2_data = st.columns([1, 2])
        with col1_data:
            image = Image.open(st.session_state.picture_path)
            st.image(image, caption=selected_person_name)
        with col2_data:
            st.write(f"**Name:** {person.firstname} {person.lastname}")
            st.write(f"**Geburtstag:** {person.date_of_birth}")
            st.write(f"**Adresse:** {person_data.get('address', 'Keine Adresse vorhanden')}")
            st.write(f"**Alter:** {person.calc_age()} Jahre")



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