import streamlit as st
import json
from PIL import Image
from ekgdata import EKGdata
from read_pandas import read_my_csv, erstelle_hr_zonen_plot, berechne_durchschnittswerte

# Personenliste laden aus JSON-Datei (anpassen, falls anders)
@staticmethod
def load_person_data():
    file = open("data/person_db.json")
    person_data = json.load(file)
    return person_data

persons_list = load_person_data()
person_names = [f"{p['firstname']} {p['lastname']}" for p in persons_list]

st.write("# EKG-App")

st.write("## Versuchsperson auswählen")

# Personenauswahl
selected_person_name = st.selectbox('Versuchsperson', options=person_names, key="sbVersuchsperson")

# Bild im Session State speichern (Default Bild)
if 'picture_path' not in st.session_state:
    st.session_state.picture_path = 'data/pictures/none.jpg'

# Bildpfad zur ausgewählten Person finden
person_data = next((p for p in persons_list if f"{p['firstname']} {p['lastname']}" == selected_person_name), None)
if person_data and "picture_path" in person_data:
    st.session_state.picture_path = person_data["picture_path"]

# Bild anzeigen
image = Image.open(st.session_state.picture_path)
st.image(image, caption=selected_person_name)

st.write("## EKG-Test")

# EKG-Test-Auswahl (wenn Person gefunden)
if person_data:
    ekg_tests = person_data.get("ekg_tests", [])

    # EKG-Tests nach ID absteigend sortieren (neueste zuerst)
    ekg_tests_sorted = sorted(ekg_tests, key=lambda x: x['id'], reverse=True)

    ekg_test_options = [f"EKG ID {test['id']} - {test['date']}" for test in ekg_tests_sorted]

    # Standardmäßig neuester EKG-Test ausgewählt (höchste ID)
    selected_ekg_test = st.selectbox( "EKG-Test auswählen", ekg_test_options, index=0)

    if selected_ekg_test:
        # EKG-Test ID extrahieren
        ekg_test_id = int(selected_ekg_test.split()[2])
        try:
            ekg = EKGdata.load_by_id(ekg_test_id, persons_list)

            st.write(f"### EKG-Daten geladen: Test-ID {ekg.id}, Datum: {ekg.date}")
            st.write(f"Person: {ekg.person_firstname} {ekg.person_lastname}")

            # Automatischen Schwellenwert bestimmen
            threshold = ekg.auto_threshold()
            st.write(f"Automatisch berechneter Schwellenwert für Peaks: {threshold:.2f}")  # .2f = Float mit 2 Dezimalstellen

            # Herzfrequenz schätzen und anzeigen
            hr = ekg.estimate_hr(threshold=threshold)
            if hr is not None:
                st.metric("Geschätzte Herzfrequenz (bpm)", hr)
            else:
                st.warning("Nicht genügend Peaks zur Herzfrequenz-Berechnung gefunden.")

            # Plot erstellen und anzeigen
            ekg.plot_time_series()
            st.plotly_chart(ekg.fig)

        except Exception as e:
            st.error(f"Fehler beim Laden des EKG-Tests: {e}")

st.write("## Herzfrequenz-/Leistungsdiagramm")

# Max HR Eingabe
max_hr = st.number_input("Gib deine maximale Herzfrequenz (Max HR) ein:",
                        min_value=100, max_value=225, value=190)

# Aktivitätsdaten laden und plotten
try:
    df = read_my_csv()
    st.success("Daten erfolgreich geladen!")

    erstelle_hr_zonen_plot(df, max_hr)

    durchschnitt_hf, durchschnitt_leistung = berechne_durchschnittswerte(df)

    st.subheader(" Durchschnittswerte")
    col1, col2 = st.columns(2)
    col1.metric("Ø Herzfrequenz (bpm)", f"{durchschnitt_hf:.1f}")
    col2.metric("Ø Leistung (W)", f"{durchschnitt_leistung:.1f}")

except FileNotFoundError:
    st.error("Die Aktivitätsdatei konnte nicht gefunden werden.")
except Exception as e:
    st.error(f"Fehler beim Einlesen oder Plotten: {e}")
