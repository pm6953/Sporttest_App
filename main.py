import streamlit as st
from read_ekgdata import EKGdata
from read_persondata import Person
from fit_reader import FTP_Test
import json
from PIL import Image
import os
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt 

st.set_page_config(layout="centered") # Layout in der Mitte

st.title("Sporttest-App")

# Initialisiere aller Session State Variablen 
if 'show_new_person_form' not in st.session_state:
    st.session_state['show_new_person_form'] = False
if 'confirm_delete_id' not in st.session_state:
    st.session_state['confirm_delete_id'] = None
if 'confirm_delete_name' not in st.session_state:
    st.session_state['confirm_delete_name'] = None
if 'show_delete_confirmation' not in st.session_state:
    st.session_state['show_delete_confirmation'] = False
if 'person_select_box' not in st.session_state:
    st.session_state['person_select_box'] = ""
if 'person_deleted_message' not in st.session_state:
    st.session_state['person_deleted_message'] = False
if 'person_added_message' not in st.session_state:
    st.session_state['person_added_message'] = False
if 'last_added_person_name' not in st.session_state:
    st.session_state['last_added_person_name'] = ""
if 'show_person_details' not in st.session_state: # New session state for showing details
    st.session_state['show_person_details'] = False


# Initialisiere den Trainingsplan hier, direkt nach den anderen Session State Variablen
if 'training_plan_df' not in st.session_state:
    # Initialdaten für den bearbeitbaren Trainingsplan
    initial_training_data = {
        "Tag": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
        "Übung": ["", "", "", "", "", "", ""],
        "Dauer (Min.)": ["", "", "", "", "", "", ""],
        "Intensität": ["", "", "", "", "", "", ""],
        "Notizen": ["", "", "", "", "", "", ""]
    }
    st.session_state['training_plan_df'] = pd.DataFrame(initial_training_data)

# Initialisiere die HF-Zonen-Tabelle im Session State
if 'hf_zones_df' not in st.session_state:
    initial_hf_zones_data = {
        "Zone": ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"],
        "maximale Herzfrequenz (%)": ["50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
    }
    st.session_state['hf_zones_df'] = pd.DataFrame(initial_hf_zones_data)


# Personenliste laden (wird vor Sidebar gebraucht)
persons_list = Person.load_person_data()
person_names = Person.get_person_list(persons_list)

# Tabs für die Navigation
# Die Reihenfolge der Tabs entspricht der Skizze: Daten, Tests, FTP-Test, Trainingsplan
tabs = st.tabs(["Daten", "Tests", "FTP-Test", "Trainingsplan"])

# Tab Person
with tabs[0]:
    # CSS für den Plus-Button
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            margin-top: 0px !important;
            height: 35px;
            width: 35px;
            font-size: 22px;
            vertical-align: bottom;
        }
        </style>
    """, unsafe_allow_html=True)

    # CSS für den Löschen-Button
    st.markdown("""
        <style>
        /* Grundlegendes Styling für alle Button-Texte, um Umbruch zu verhindern */
        button[data-testid="stButton"] > div > p {
            font-size: 18px; /* Schriftgröße anpassen für alle Buttons */
            font-weight: bold; /* Fettgedruckt für alle Buttons */
            white-space: nowrap !important; /* Wichtig: !important hinzugefügt */
            overflow: hidden !important; /* Wichtig: !important hinzugefügt */
            text-overflow: ellipsis !important; /* Wichtig: !important hinzugefügt */
            display: block !important; /* Sicherstellen, dass der Textblock sich verhält wie erwartet */
        }

        /* Styling für den spezifischen Löschen-Button selbst */
        button[key="delete_person_button_main"] {
            background-color: #ff4b4b; /* Roter Hintergrund */
            color: white; /* Weiße Schrift */
            padding: 10px 20px !important; /* Innenabstand erhöhen, !important */
            border-radius: 5px !important; /* Abgerundete Ecken, !important */
            border: none !important; /* Kein Rand, !important */
            width: 100% !important; /* Volle Breite im Container, !important */
            max-width: 200px !important; /* Maximale Breite, um nicht zu riesig zu werden */
            height: auto !important; /* Höhe automatisch anpassen, !important */
            min-height: 50px !important; /* Mindesthöhe für den Button, !important */
            margin-top: 15px !important; /* Etwas Abstand nach oben, !important */
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2) !important; /* Leichter Schatten, !important */
            display: flex !important; /* Flexbox für bessere Zentrierung/Ausrichtung des Inhalts, !important */
            justify-content: center !important; /* Zentriert den Inhalt horizontal, !important */
            align-items: center !important; /* Zentriert den Inhalt vertikal, !important */
            text-align: center !important; /* Text innerhalb des Buttons zentrieren */
        }
        button[key="delete_person_button_main"]:hover {
            background-color: #cc0000 !important; /* Dunklerer Rotton beim Hover, !important */
            cursor: pointer !important; /* Zeigt an, dass es klickbar ist, !important */
        }

        /* Styling für die Ja/Nein Buttons der Bestätigung */
        button[key="confirm_delete_yes_button"],
        button[key="confirm_delete_no_button"] {
            padding: 8px 15px !important;
            font-size: 16px !important;
            border-radius: 4px !important;
            border: none !important;
            cursor: pointer !important;
            width: 100% !important; /* Volle Breite innerhalb ihrer Spalte */
            margin-top: 5px !important; /* Kleiner Abstand zwischen den Buttons */
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        button[key="confirm_delete_yes_button"] {
            background-color: #d32f2f !important; /* Dunkleres Rot für Ja */
            color: white !important;
        }
        button[key="confirm_delete_yes_button"]:hover {
            background-color: #b71c1c !important;
        }
        button[key="confirm_delete_no_button"] {
            background-color: #f0f2f6 !important; /* Helles Grau für Abbrechen */
            color: #333 !important;
            border: 1px solid #ddd !important;
        }
        button[key="confirm_delete_no_button"]:hover {
            background-color: #e0e2e6 !important;
        }
        </style>
    """, unsafe_allow_html=True)


    # Hauptinhaltsbereich des "Daten" Tabs
    st.write("### Person auswählen:")
    col_select, col_add_button = st.columns([0.8, 0.2])

    with col_select:
        current_selection_from_widget = st.selectbox(
            "_", # Label is blank for cleaner look next to button
            options=[""] + person_names,
            index=([""] + person_names).index(st.session_state['person_select_box'])
            if st.session_state['person_select_box'] in ([""] + person_names) else 0,
            key="person_select_box",
            label_visibility="hidden" # Hide the label explicitly
        )

    with col_add_button:
        # "+" Button um eine neue Person hinzuzufügen
        add_new = st.button("➕", help="Neue Person hinzufügen", key="add_new_person_button_main")
        if add_new:
            st.session_state['show_new_person_form'] = True
            st.session_state['person_select_box'] = "" # Clear selection when adding new
            st.session_state['show_delete_confirmation'] = False
            st.session_state['confirm_delete_id'] = None
            st.session_state['confirm_delete_name'] = None
            st.session_state['person_deleted_message'] = False
            st.session_state['person_added_message'] = False
            st.session_state['show_person_details'] = False # Hide details when adding new

    # Logik für Erfolgs-/Fehlermeldungen
    if st.session_state.get('person_deleted_message', False):
        st.success("Person wurde erfolgreich gelöscht.")
        st.session_state['person_deleted_message'] = False
        st.session_state['show_person_details'] = False # Hide details after delete

    elif st.session_state.get('person_added_message', False):
        st.success(f"Person **{st.session_state['last_added_person_name']}** wurde hinzugefügt.")
        st.session_state['person_added_message'] = False
        st.session_state['last_added_person_name'] = ""
        st.session_state['show_person_details'] = True # Show details of the newly added person

    # Logik für das Formular "Neue Person anlegen"
    elif st.session_state.get('show_new_person_form', False):
        st.subheader("➕ Neue Person anlegen")
        with st.form("neue_person_formular"):
            firstname = st.text_input("Vorname", key="new_person_firstname")
            lastname = st.text_input("Nachname", key="new_person_lastname")
            birth_date = st.date_input("Geburtsdatum", value=date.today(), key="new_person_birthdate")
            gender = st.selectbox("Geschlecht", ["male", "female"], key="new_person_gender")
            address = st.text_input("Adresse", key="new_person_address")

            # Placeholder for Telefonnummer (not in Person class currently, so just a text input)
            phone_number = st.text_input("Telefonnummer", key="new_person_phone_number")

            picture_file = st.file_uploader("Profilbild hochladen (optional)", type=["jpg", "jpeg", "png"], key="new_person_picture_file")

            st.markdown("### Optional: Dateien hochladen")
            ruhe_ekg_file = st.file_uploader("Ruhe-EKG PDF", type=["pdf"], key="ruhe_ekg_upload")
            ftp_test_file = st.file_uploader("FTP-Test PDF", type=["pdf"], key="ftp_test_upload")

            submitted = st.form_submit_button("Person hinzufügen")

        if submitted:
            if not firstname or not lastname or not birth_date or not gender:
                st.error("Bitte füllen Sie alle erforderlichen Felder (Vorname, Nachname, Geburtsdatum, Geschlecht) aus.")
            else:
                persons_list_current = Person.load_person_data()
                exists = any(p["firstname"].strip().lower() == firstname.strip().lower() and
                             p["lastname"].strip().lower() == lastname.strip().lower() for p in persons_list_current)

                if exists:
                    st.warning("Diese Person existiert bereits.")
                else:
                    new_id = max([p.get("id", 0) for p in persons_list_current] + [0]) + 1

                    ekg_file_path = ""
                    ftp_file_path = ""
                    profile_picture_path = ""

                    os.makedirs("data/files", exist_ok=True)
                    os.makedirs("data/pictures", exist_ok=True)

                    if ruhe_ekg_file is not None:
                        ekg_file_path = f"data/files/ruhe_ekg_{new_id}_{ruhe_ekg_file.name}"
                        with open(ekg_file_path, "wb") as f:
                            f.write(ruhe_ekg_file.getbuffer())

                    if ftp_test_file is not None:
                        ftp_file_path = f"data/files/ftp_test_{new_id}_{ftp_test_file.name}"
                        with open(ftp_file_path, "wb") as f:
                            f.write(ftp_test_file.getbuffer())

                    if picture_file is not None:
                        profile_picture_path = f"data/pictures/profile_{new_id}_{picture_file.name}"
                        with open(profile_picture_path, "wb") as f:
                            f.write(picture_file.getbuffer())

                    neue_person = {
                        "id": new_id,
                        "firstname": firstname.strip(),
                        "lastname": lastname.strip(),
                        "date_of_birth": birth_date.strftime("%Y-%m-%d"),
                        "gender": gender,
                        "address": address.strip(),
                        "phone_number": phone_number.strip(), # Add phone number
                        "picture_path": profile_picture_path,
                        "ruhe_ekg_file": ekg_file_path,
                        "ftp_test_file": ftp_file_path
                    }

                    persons_list_current.append(neue_person)
                    Person.save_person_data(persons_list_current)

                    st.session_state['person_added_message'] = True
                    st.session_state['last_added_person_name'] = f"{firstname} {lastname}"
                    st.session_state['show_new_person_form'] = False
                    st.session_state['person_select_box'] = f"{firstname} {lastname}" # Select the newly added person
                    st.session_state['show_person_details'] = True # Show details of the newly added person

    # Logik für die Anzeige von Personendetails und den Lösch-Button
    selected_person_name_data_tab = st.session_state.get('person_select_box', '') # Holen wir die Person hier für diesen Tab

    if selected_person_name_data_tab and not st.session_state['show_new_person_form']:
        person_data = Person.find_person_data_by_name(selected_person_name_data_tab)

        if person_data:
            person = Person(person_data) # Create a Person object to access attributes easily

            # Display image and details side-by-side as in the sketch
            col_img, col_info = st.columns([1, 2])

            with col_img:
                #st.write("### Bild") # Placeholder for "Bild"
                picture_path = person.picture_path
                if not picture_path or not os.path.isfile(picture_path):
                    st.write("_(Kein Bild vorhanden)_") # Text placeholder
                else:
                    image = Image.open(picture_path)
                    st.image(image, use_container_width=True)

            with col_info:
                st.markdown(f"**Name:** {person.firstname} {person.lastname}")
                st.markdown(f"**Geburtsdatum:** {person.date_of_birth}")
                st.markdown(f"**Adresse:** {person.address or 'Keine Adresse vorhanden'}")
                st.markdown(f"**Telefonnummer:** {person_data.get('phone_number', 'Keine Telefonnummer vorhanden')}") # Access via dict if not in Person class

            st.markdown("---")

            # Lösch-Button und Bestätigungsdialog in einem separaten Container
            with st.container():
                # Nur anzeigen, wenn keine Bestätigung aussteht
                if not st.session_state.get('show_delete_confirmation', False):
                    if st.button("Löschen", key="delete_person_button_main"):
                        st.session_state['confirm_delete_id'] = person.id
                        st.session_state['confirm_delete_name'] = st.session_state['person_select_box']
                        st.session_state['show_delete_confirmation'] = True
                        st.session_state['person_deleted_message'] = False

                # Bestätigungsdialog anzeigen, wenn show_delete_confirmation True ist
                if st.session_state.get('show_delete_confirmation', False) and \
                   st.session_state.get('confirm_delete_id') == person.id:
                    st.warning(f"Sind Sie sicher, dass Sie **{st.session_state['confirm_delete_name']}** unwiderruflich löschen möchten?")
                    col_confirm1, col_confirm2 = st.columns(2)
                    with col_confirm1:
                        if st.button("Ja, endgültig löschen", key="confirm_delete_yes_button"):
                            if Person.delete_person_by_id(person.id):
                                st.session_state['person_deleted_message'] = True
                                st.session_state['confirm_delete_id'] = None
                                st.session_state['confirm_delete_name'] = None
                                st.session_state['show_delete_confirmation'] = False
                                st.session_state['show_new_person_form'] = False
                                st.session_state['person_select_box'] = ""
                                st.session_state['person_added_message'] = False
                                st.session_state['show_person_details'] = False
                            else:
                                st.error(f"Fehler beim Löschen von {st.session_state['confirm_delete_name']}.")
                                st.session_state['confirm_delete_id'] = None
                                st.session_state['confirm_delete_name'] = None
                                st.session_state['show_delete_confirmation'] = False

                    with col_confirm2:
                        if st.button("Abbrechen", key="confirm_delete_no_button"):
                            st.info("Löschvorgang abgebrochen.")
                            st.session_state['confirm_delete_id'] = None
                            st.session_state['confirm_delete_name'] = None
                            st.session_state['show_delete_confirmation'] = False
        else:
            st.warning("Die Daten zur ausgewählten Person konnten nicht gefunden werden. Möglicherweise wurde die Person gelöscht.")
            st.session_state['person_select_box'] = ""
            st.session_state['show_delete_confirmation'] = False
            st.session_state['show_person_details'] = False


    # Anfangsnachricht, wenn nichts ausgewählt ist und kein anderer Zustand aktiv ist
    if not st.session_state['person_select_box'] and \
       not st.session_state['show_new_person_form'] and \
       not st.session_state['person_added_message'] and \
       not st.session_state['person_deleted_message'] and \
       not st.session_state['show_delete_confirmation']:
        st.info("Bitte wählen Sie eine Person aus oder legen Sie eine neue an.")


# Tests
with tabs[1]:
    st.header("Ruhe-EKG")
    # selected_person_name_test_tab definieren, damit person_data abgerufen werden kann
    selected_person_name_test_tab = st.session_state.get('person_select_box', '')

    if selected_person_name_test_tab: # Nur fortfahren, wenn eine Person ausgewählt ist
        person_data_test_tab = Person.find_person_data_by_name(selected_person_name_test_tab)
        
        if person_data_test_tab: # Prüfen, ob die Personendaten gefunden wurden
            ekg_tests = person_data_test_tab.get("ekg_tests", [])

            if ekg_tests: # Nur wenn EKG-Tests vorhanden sind
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

                        # Herzfrequenz schätzen und anzeigen -> muss noch geändert werden
                        hr = ekg.estimate_hr(threshold=threshold)
                        if hr is not None:
                            st.metric("Geschätzte Herzfrequenz (bpm)", hr)
                        else:
                            st.warning("Nicht genügend Peaks zur Herzfrequenz-Berechnung gefunden.")

                        # Plot erstellen und anzeigen
                        # Das Figure-Objekt von plot_time_series() abfangen und an st.pyplot übergeben
                        fig_to_display = ekg.plot_time_series(threshold=threshold) # threshold übergeben(Optional)
                        st.pyplot(fig_to_display) #  ST.PYPLOT 
                        plt.close(fig_to_display) #  Schließen der Matplotlib-Figur, um Speicherlecks zu vermeiden

                    except Exception as e:
                        st.error(f"Fehler beim Laden des EKG-Tests: {e}")
            else:
                st.info("Für die ausgewählte Person sind keine EKG-Tests vorhanden.")
        else:
            st.warning("Die Daten zur ausgewählten Person konnten nicht gefunden werden. Bitte überprüfen Sie Ihre Auswahl.")
    else:
        st.info("Bitte wählen Sie zuerst eine Person im Tab 'Daten' aus, um EKG-Tests anzuzeigen.")

    st.header("Lungentest")
    st.write("Hier könnten Details und Visualisierungen zu Lungentest-Daten angezeigt werden.")

with tabs[2]:
    st.header("Stufentest Fahrradergometer")
    selected_person_name_test_tab = st.session_state.get('person_select_box', '')

    if selected_person_name_test_tab:
        person_data_test_tab = Person.find_person_data_by_name(selected_person_name_test_tab)

        if person_data_test_tab:
            ftp_tests = person_data_test_tab.get("ftp_tests", [])

            if ftp_tests:
                ftp_tests_sorted = sorted(ftp_tests, key=lambda x: x['id'], reverse=True)
                ftp_test_options = [f"FTP ID {test['id']} - {test['date']}" for test in ftp_tests_sorted]

                selected_ftp_test = st.selectbox("FTP-Test auswählen", ftp_test_options, index=0)

                if selected_ftp_test:
                    ftp_test_id = int(selected_ftp_test.split()[2])
                    try:
                        test = next(test for p in persons_list for test in p.get("ftp_tests", []) if test["id"] == ftp_test_id)
                        ftp = FTP_Test(
                            file_path=test["result_link"],
                            id=test.get("id"),
                            date=test.get("date"),
                            person_firstname=person_data_test_tab.get("firstname"),
                            person_lastname=person_data_test_tab.get("lastname")
                            )


                        st.write(f"### FTP-Test geladen: Test-ID {ftp.id}, Datum: {ftp.date}")
                        st.write(f"Person: {ftp.person_firstname} {ftp.person_lastname}")

                        df = ftp.df
                        if not df.empty:
                            st.write("### Zusammenfassung des Tests")
                            dauer = df.index[-1] - df.index[0]
                            dauer_min = round(dauer.total_seconds() / 60, 1)
                            mean_hr = round(df["heart_rate"].mean(), 1) if "heart_rate" in df else "?"
                            max_power = df["power"].max() if "power" in df else "?"

                            st.metric("Gesamtdauer", f"{dauer_min} Minuten")
                            st.metric("Ø Herzfrequenz", f"{mean_hr} bpm")
                            st.metric("Maximale Leistung", f"{max_power} Watt")

                            st.write("### Verlauf des FTP-Tests")
                            start_time = df.index[0]
                            df["minuten"] = (df.index - start_time).total_seconds() / 60

                            # Plot erstellen basierend auf Auswahl
                            # Checkboxen zur Auswahl
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                show_hr = st.checkbox("Herzfrequenz", value=True)
                            with col2:
                               show_power = st.checkbox("Leistung", value=True)
                            with col3:
                                show_cadence = st.checkbox("Trittfrequenz", value=True)

                            # Plot vorbereiten
                            fig, ax = plt.subplots(figsize=(10, 5))

                            if show_hr and "heart_rate" in df.columns:
                                ax.plot(df["minuten"], df["heart_rate"], label="heart_rate")
                            if show_power and "power" in df.columns:
                                ax.plot(df["minuten"], df["power"], label="power")
                            if show_cadence and "cadence" in df.columns:
                                ax.plot(df["minuten"], df["cadence"], label="cadence")

                            ax.set_xlabel("Minuten")
                            ax.set_ylabel("Wert")
                            ax.set_title("Verlauf: Herzfrequenz, Leistung, Trittfrequenz")
                            ax.legend()
                            st.pyplot(fig)


                        else:
                            st.warning("Keine darstellbaren Daten im FTP-Test gefunden.")

                    except Exception as e:
                        st.error(f"Fehler beim Laden des FTP-Tests: {e}")
            else:
                st.info("Für die ausgewählte Person sind keine FTP-Tests vorhanden.")
        else:
            st.warning("Die Daten zur ausgewählten Person konnten nicht gefunden werden. Bitte überprüfen Sie Ihre Auswahl.")
    else:
        st.info("Bitte wählen Sie zuerst eine Person im Tab 'Daten' aus, um FTP-Tests anzuzeigen.")


# TAB 3: Trainingsplan
with tabs[3]:
    st.header("Trainingsplan")

    st.markdown("### HF-Zonen:")

    # Logik zur Berechnung und Anzeige der HF-Zonen basierend auf der ausgewählten Person
    selected_person_name = st.session_state.get('person_select_box', '')
    max_hr_for_zones = None

    if selected_person_name:
        person_data_for_zones = Person.find_person_data_by_name(selected_person_name)
        if person_data_for_zones:
            person_obj_for_zones = Person(person_data_for_zones)
            # Ruft die angepasste calc_max_heart_rate auf, die FTP-Wert bevorzugt
            max_hr_for_zones = person_obj_for_zones.calc_max_heart_rate()
            if max_hr_for_zones is None:
                st.warning(f"Keine maximale Herzfrequenz für **{selected_person_name}** verfügbar. Bitte FTP-Test-Wert eingeben oder Geburtsdatum/Geschlecht prüfen.")

    # Aktualisiere den HF-Zonen DataFrame
    if max_hr_for_zones is not None:
        hf_zones_data = {
            "Zone": ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"],
            "Prozentsatz der MHF": ["50-60%", "60-70%", "70-80%", "80-90%", "90-100%"],
            "Berechnete Zonen (bpm)": [] # Spaltenname hier aktualisiert
        }

        # Berechne die HF-Werte für jede Zone
        ranges = [(0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 0.90), (0.90, 1.00)]
        for lower_bound, upper_bound in ranges:
            min_hr = round(max_hr_for_zones * lower_bound)
            max_hr = round(max_hr_for_zones * upper_bound)
            hf_zones_data["Berechnete Zonen (bpm)"].append(f"{min_hr}-{max_hr}") # Daten in die neue Spalte füllen

        st.session_state['hf_zones_df'] = pd.DataFrame(hf_zones_data)
        st.info(f"Die Herzfrequenz-Zonen basieren auf einer maximalen Herzfrequenz von **{round(max_hr_for_zones)} bpm** für **{selected_person_name}**.")
    else:
        # Standard-Werte, wenn keine Person ausgewählt ist oder MHF nicht berechnet werden kann
        st.info("Bitte wählen Sie eine Person im Tab 'Daten' aus und geben Sie ggf. die maximale Herzfrequenz an, um personalisierte HF-Zonen anzuzeigen.")
        st.session_state['hf_zones_df'] = pd.DataFrame({
            "Zone": ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"],
            "Prozentsatz der MHF": ["50-60%", "60-70%", "70-80%", "80-90%", "90-100%"],
            "Berechnete Zonen (bpm)": ["", "", "", "", ""] # Leere Werte
        })


    # Funktion zum Stylen des DataFrames (für Zeilenfarben)
    def highlight_zones(row): # Benenne den Parameter in 'row' um, um Klarheit zu schaffen
        colors = {
            "Zone 1": '#e6ffe6', # Hellgrün (Erholung)
            "Zone 2": '#cce6ff', # Hellblau (Ausdauer)
            "Zone 3": '#ffffcc', # Hellgelb (Aerob)
            "Zone 4": '#ffcccc', # Hellrot (Anaerob)
            "Zone 5": '#ff9999'  # Rot (Maximal)
        }
        zone_name = row['Zone'] # Greife auf den Wert in der 'Zone'-Spalte der aktuellen Zeile zu
        color = colors.get(zone_name, '') # Hole die Farbe für diese Zone

        # Gebe eine Liste von Stil-Strings zurück, einen für jede Spalte der Zeile
        # Alle Spalten in dieser Zeile erhalten die gleiche Hintergrundfarbe
        return [f'background-color: {color}' for _ in row.index]


    # Anzeige der HF-Zonen-Tabelle mit Styling
    st.dataframe(
        st.session_state['hf_zones_df'].style.apply(highlight_zones, axis=1),
        hide_index=True,
        use_container_width=True
    )

    st.markdown("---") # Trennlinie

    st.markdown("### Trainingsplan:")
    st.write("Tragen Sie hier Ihre Trainingseinheiten ein:")

    # data_editor für den editierbaren Trainingsplan
    edited_df_training_plan = st.data_editor(
        st.session_state['training_plan_df'],
        num_rows="dynamic", # Ermöglicht das Hinzufügen/Löschen von Zeilen
        height=300,        # Feste Höhe für die Tabelle
        use_container_width=True, # Passt sich der Container-Breite an
        column_order=("Tag", "Übung", "Dauer (Min.)", "Intensität"), # Reihenfolge der Spalten
        column_config={
            "Tag": st.column_config.Column(
                "Tag",
                help="Der Wochentag",
                width="small",
                disabled=True # Tag soll nicht editierbar sein
            ),
            "Übung": st.column_config.TextColumn( 
                "Übung",
                help="Beschreibung der Übung",
                width="medium"
            ),
            "Dauer (Min.)": st.column_config.NumberColumn(
                "Dauer (Min.)",
                help="Dauer der Übung in Minuten",
                min_value=0,
                max_value=300,
                step=5,
                width="small"
            ),
            "Intensität": st.column_config.SelectboxColumn(
                "Intensität",
                help="Intensitätslevel",
                options=["Zone 1", "Zone 2", "Zone 3", "Zone 4","Zone 5"],
                required=False,
                width="small"
            )
        }
    )

    # Speichern des bearbeiteten Trainings-DataFrames 
    st.session_state['training_plan_df'] = edited_df_training_plan