import streamlit as st
from read_ekgdata import EKGdata
from read_persondata import Person
from fit_reader import FTP_Test
import json
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt 
from fpdf import FPDF
import tempfile

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
if 'show_person_details' not in st.session_state:
    st.session_state['show_person_details'] = False
if 'missing_optional_fields_message' not in st.session_state:
    st.session_state['missing_optional_fields_message'] = ""
# NEU: Variable, um festzuhalten, welche Person zuletzt HINZUGEFÜGT wurde
if 'just_added_person_name' not in st.session_state:
    st.session_state['just_added_person_name'] = ""
if 'show_edit_person_form' not in st.session_state:
    st.session_state['show_edit_person_form'] = False



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


# Personenliste laden 
persons_list = Person.load_person_data()
person_names = Person.get_person_list(persons_list)

# Callback-Funktion für den "Neue Person hinzufügen" Button
def add_new_person_callback():
    st.session_state['show_new_person_form'] = True
    st.session_state['person_select_box'] = "" # Auswahl leeren, wenn neue Person hinzugefügt wird
    st.session_state['show_delete_confirmation'] = False # Löschbestätigung ausblenden
    st.session_state['confirm_delete_id'] = None
    st.session_state['confirm_delete_name'] = None
    st.session_state['person_deleted_message'] = False
    st.session_state['person_added_message'] = False
    st.session_state['show_person_details'] = False # Details ausblenden
    st.session_state['missing_optional_fields_message'] = "" # Meldung zurücksetzen
    st.session_state['just_added_person_name'] = "" # Wichtig: reset this

# Callback-Funktion für den "Löschen" Button (Bestätigungsschritt)
def prepare_delete_callback(person_id, person_name):
    st.session_state['confirm_delete_id'] = person_id
    st.session_state['confirm_delete_name'] = person_name
    st.session_state['show_delete_confirmation'] = True
    st.session_state['person_deleted_message'] = False # Sicherstellen, dass keine alte Löschmeldung aktiv ist
    st.session_state['show_person_details'] = False # Details ausblenden, während Bestätigung angezeigt wird
    st.session_state['missing_optional_fields_message'] = "" # Meldung zurücksetzen
    st.session_state['just_added_person_name'] = "" # Wichtig: reset this

# Callback-Funktion für die tatsächliche Löschung
def execute_delete_callback(person_id, person_name):
    if Person.delete_person_by_id(person_id):
        st.session_state['person_deleted_message'] = True
        st.session_state['confirm_delete_id'] = None
        st.session_state['confirm_delete_name'] = None
        st.session_state['show_delete_confirmation'] = False
        st.session_state['show_new_person_form'] = False
        st.session_state['person_select_box'] = "" # Leert die Selectbox nach dem Löschen
        st.session_state['person_added_message'] = False
        st.session_state['show_person_details'] = False # Details ausblenden
        st.session_state['just_added_person_name'] = "" # Wichtig: reset this
    else:
        st.error(f"Fehler beim Löschen von {person_name}.") # Fehlermeldung bei Problemen
        st.session_state['confirm_delete_id'] = None
        st.session_state['confirm_delete_name'] = None
        st.session_state['show_delete_confirmation'] = False
    st.session_state['missing_optional_fields_message'] = "" # Meldung zurücksetzen

# Callback-Funktion für Abbruch der Löschung
def cancel_delete_callback():
    st.session_state['confirm_delete_id'] = None
    st.session_state['confirm_delete_name'] = None
    st.session_state['show_delete_confirmation'] = False
    # Nach Abbruch der Löschung können die Details wieder angezeigt werden
    if st.session_state['person_select_box'] != "" and not st.session_state['show_new_person_form']:
        st.session_state['show_person_details'] = True
    else:
        st.session_state['show_person_details'] = False
    st.info("Löschvorgang abgebrochen.")
    st.session_state['missing_optional_fields_message'] = "" # Meldung zurücksetzen
    st.session_state['just_added_person_name'] = "" # Wichtig: reset this

# Callback: Wenn sich die Person in der Selectbox ändert
def on_person_select_change():
    # Setze show_person_details auf True, wenn eine Person ausgewählt wurde (nicht der leere String)
    if st.session_state['person_select_box'] != "":
        st.session_state['show_person_details'] = True
        st.session_state['show_new_person_form'] = False # Formular für neue Person ausblenden
        st.session_state['show_delete_confirmation'] = False # Löschbestätigung ausblenden
        st.session_state['person_deleted_message'] = False # Löschmeldung ausblenden
        st.session_state['person_added_message'] = False # Hinzufügen-Meldung ausblenden
    else:
        st.session_state['show_person_details'] = False
        st.session_state['show_new_person_form'] = False
        st.session_state['show_delete_confirmation'] = False
        st.session_state['person_deleted_message'] = False
        st.session_state['person_added_message'] = False
    st.session_state['missing_optional_fields_message'] = "" # Meldung zurücksetzen
    st.session_state['just_added_person_name'] = "" # Wichtig: reset this

# Callback: Nach erfolgreichem Hinzufügen einer Person
def on_person_add_success_indicator(firstname, lastname, missing_fields_message=""):
    st.session_state['person_added_message'] = True
    st.session_state['last_added_person_name'] = f"{firstname} {lastname}"
    st.session_state['show_new_person_form'] = False
    st.session_state['show_person_details'] = True
    st.session_state['missing_optional_fields_message'] = missing_fields_message 
    st.session_state['just_added_person_name'] = f"{firstname} {lastname}" # <-- Wichtig: Setzt den Namen hier!


# Tabs für die Navigation
tabs = st.tabs(["Daten", "Tests", "FTP-Test", "Trainingsplan"])

# Tab Person
with tabs[0]:
    st.markdown("""
        <style>
        /* Spezifisches Styling für den Plus-Button */
        div.stButton > button[data-testid="stButton-add_new_person_button_main"] {
            height: 35px !important;
            width: 35px !important;
            font-size: 22px !important;
            vertical-align: bottom !important;
            color: #4B4B4B !important;
            border: none !important; /* KEINE UMRANDUNG für den Plus-Button */
            background-color: #F0F2F6 !important;
        }

        div.stButton > button[data-testid="stButton-add_new_person_button_main"]:hover {
            border: none !important;
            background-color: #E0E2E6 !important;
            color: #4B4B4B !important;
        }

        div.stButton > button[data-testid="stButton-add_new_person_button_main"]:active {
            border: none !important;
            background-color: #D0D2D6 !important;
            color: #4B4B4B !important;
        }
        
        /* interne Label der Selectbox beeinflussen */
        div[data-testid="stSelectbox"] {
            margin-top: 0rem;
            
        }
        div[data-testid="stSelectbox"] > label {
            padding-bottom: 0px !important;
            margin-bottom: 0px !important;
            
        }

        /* Allgemeine Button-Styles (betrifft jetzt auch den Löschen-Button) */
        /* Diese Regel muss weniger spezifisch sein als die für den Plus-Button */
        .stButton button {
            white-space: nowrap !important;
            text-align: center !important;
            width: auto !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            height: 38px !important; 
            background-color: rgb(240, 242, 246) !important; 
            color: rgb(75, 75, 75) !important; 
            border-radius: 0.25rem !important; 
            border: none !important;
        }
        
        /* Hover und Active Styles für allgemeine Buttons */
        .stButton button:hover {
            background-color: rgb(230, 230, 230) !important; 
            border-color: rgb(180, 180, 180) !important; 
        }
        .stButton button:active {
            background-color: rgb(220, 220, 220) !important; 
            border-color: rgb(150, 150, 150) !important; 
        }

        </style>
    """, unsafe_allow_html=True)
    
    # Hauptinhaltsbereich des "Daten" Tabs
    st.write("### Person:")
    col_select, col_add_button = st.columns([0.8, 0.2])

    # Bestimme den Standardindex der Selectbox
    current_selected_name = st.session_state.get('person_select_box', '')
    if st.session_state['just_added_person_name']:
        # Wenn eine Person gerade hinzugefügt wurde, diese auszuwählen
        target_selection = st.session_state['just_added_person_name']
        st.session_state['just_added_person_name'] = "" # Reset, um nicht dauerhaft diese Person zu erzwingen
        
    else:
        target_selection = current_selected_name
    
    # Finden des Index für die Selectbox
    try:
        default_index = ([""] + person_names).index(target_selection)
    except ValueError:
        default_index = 0

    with col_select:
        current_selection_from_widget = st.selectbox(
            label="Person auswählen",
            options=person_names,
            index=None,
            placeholder="Person auswählen",
            key="person_select_box",
            on_change=on_person_select_change,
            label_visibility="hidden"
)

    
    with col_add_button:
        # Trick: Erzeuge einen leeren Platzhalter, der die Höhe eines Labels imitiert.
        st.markdown("<p style='height: 1.5rem; margin: 0; padding: 0;'>&nbsp;</p>", unsafe_allow_html=True) 
        
        # "+" Button um eine neue Person hinzuzufügen
        st.button("&nbsp;+&nbsp;", help="Neue Person hinzufügen", key="add_new_person_button_main", on_click=add_new_person_callback)
            
    st.markdown("<p class='hidden-markdown'</p>", unsafe_allow_html=True)

    # Logik für Erfolgs-/Fehlermeldungen
    if st.session_state.get('person_deleted_message', False):
        st.success("Person wurde erfolgreich gelöscht.")
        st.session_state['person_deleted_message'] = False

    elif st.session_state.get('person_added_message', False):
        st.success(f"Person **{st.session_state['last_added_person_name']}** wurde hinzugefügt.")
        # Zeige optionale Felder Warnung, falls vorhanden
        if st.session_state['missing_optional_fields_message']:
            st.info(st.session_state['missing_optional_fields_message'])
        st.session_state['person_added_message'] = False
        st.session_state['last_added_person_name'] = ""
        st.session_state['missing_optional_fields_message'] = "" # Nachricht zurücksetzen


    # Logik für das Formular "Neue Person anlegen"
    if st.session_state.get('show_new_person_form', False):
        st.subheader("&nbsp;+&nbsp; Neue Person anlegen")
        with st.form("neue_person_formular"):
            
            firstname = st.text_input("Vorname", key="new_person_firstname")
            lastname = st.text_input("Nachname", key="new_person_lastname")
            birth_date = st.date_input(
                "Geburtsdatum",
                value=date(2000,1,1),
                min_value=date(1940,1,1),
                max_value=date.today(),
                key="new_person_birthdate")
            gender_options=["male","female"]
            gender = st.selectbox(
                "Geschlecht",
                options=gender_options,
                key="new_person_gender",
                index=None,
                placeholder="Geschlecht auswählen"
                )
            address = st.text_input("Adresse", key="new_person_address") 
            phone_number = st.text_input("Telefonnummer (optional)", key="new_person_phone_number")
            st.markdown("### Optional: Dateien hochladen")
            picture_file = st.file_uploader("Profilbild hochladen ", type=["jpg", "jpeg", "png"], key="new_person_picture_file")
            ruhe_ekg_file = st.file_uploader("EKG-Datei hocladen (TXT oder CSV)", type=["txt","csv"], key="ruhe_ekg_upload")
            ftp_test_file = st.file_uploader("FTP-Test hochladen (CSV oder FIT)", type=["csv","fit"], key="ftp_test_upload")
            
            submitted = st.form_submit_button("Person hinzufügen")

        if submitted:
            # Validierung der Pflichtfelder - nur die mit Sternchen sind jetzt Pflichtfelder
            if not firstname or not lastname or not birth_date or not gender or not address:
                st.error("Bitte füllen Sie alle erforderlichen Felder (Vorname, Nachname, Geburtsdatum, Geschlecht, Addresse) aus.")
            else:
                persons_list_current = Person.load_person_data() # Erneut laden, um sicherzustellen, dass die neueste Liste verwendet wird
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

                    # IDs für EKG und FTP Tests automatisch generieren
                    existing_ekg_ids = [test["id"] for p in persons_list_current for test in p.get("ekg_tests", [])]
                    existing_ftp_ids = [test["id"] for p in persons_list_current for test in p.get("ftp_tests", [])]
                    new_ekg_id = max(existing_ekg_ids + [0]) + 1
                    new_ftp_id = max(existing_ftp_ids + [0]) + 1

                    # EKG Tests zuordnen, falls Datei vorhanden
                    ekg_tests = []
                    if ruhe_ekg_file is not None:
                        ekg_tests.append({
                            "id": new_ekg_id,
                            "date": date.today().isoformat(),
                            "result_link": ekg_file_path
                        })

                    # FTP Tests zuordnen, falls Datei vorhanden
                    ftp_tests = []
                    if ftp_test_file is not None:
                        ftp_tests.append({
                            "id": new_ftp_id,
                            "date": date.today().isoformat(),
                            "result_link": ftp_file_path
                        })

                    # Die neue Person mit allen zugehörigen Daten
                    neue_person = {
                        "id": new_id,
                        "firstname": firstname.strip(),
                        "lastname": lastname.strip(),
                        "date_of_birth": birth_date.strftime("%Y-%m-%d"),
                        "gender": gender,
                        "address": address.strip(),
                        "phone_number": phone_number.strip(),
                        "picture_path": profile_picture_path,
                        "ruhe_ekg_file": ekg_file_path,
                        "ftp_test_file": ftp_file_path,
                        "ekg_tests": ekg_tests,
                        "ftp_tests": ftp_tests
                    }


                    persons_list_current.append(neue_person)
                    Person.save_person_data(persons_list_current)

                    # Überprüfen, ob optionale Felder fehlen
                    missing_optional_msg = ""
                    if not address.strip():
                        missing_optional_msg += "Adresse wurde nicht hinzugefügt. "
                    if not phone_number.strip():
                        missing_optional_msg += "Telefonnummer wurde nicht hinzugefügt. "
                    if not picture_file:
                        missing_optional_msg += "Kein Profilbild hochgeladen. "
                    if not ruhe_ekg_file:
                        missing_optional_msg += "Kein Ruhe-EKG hochgeladen. "
                    if not ftp_test_file:
                        missing_optional_msg += "Kein FTP-Test hochgeladen. "
                    if missing_optional_msg:
                        missing_optional_msg = "Hinweis: " + missing_optional_msg.strip()


                    # Aufruf Callback
                    on_person_add_success_indicator(firstname, lastname, missing_optional_msg)
                    st.rerun() 


    # Logik für die Anzeige von Personendetails
    selected_person_name_data_tab = st.session_state.get('person_select_box', '') 

    # Zeige Personendetails nur, wenn show_person_details True ist
    if selected_person_name_data_tab and st.session_state.get('show_person_details', False) and not st.session_state['show_new_person_form']:
        person_data = Person.find_person_data_by_name(selected_person_name_data_tab)

        if person_data:
            person = Person(person_data) 

            #Bild und Details nebeneinander 
            col_img, col_info = st.columns([1, 2])

            with col_img:
                picture_path = person.picture_path
                if not picture_path or not os.path.isfile(picture_path):
                    st.write("_(Kein Bild vorhanden)_") 
                else:
                    image = Image.open(picture_path)
                    st.image(image, use_container_width=True)

            with col_info:
                st.markdown(f"**Name:** {person.firstname} {person.lastname}")
                st.markdown(f"**Geburtsdatum:** {person.date_of_birth}")
                st.markdown(f"**Adresse:** {person.address or 'Keine Adresse vorhanden'}")
                st.markdown(f"**Telefonnummer:** {person_data.get('phone_number', 'Keine Telefonnummer vorhanden')}") 
                st.button("Person bearbeiten", key="edit_person_button", on_click=lambda: st.session_state.update({
                                'show_edit_person_form': True,
                                'show_new_person_form': False
                            }))
            st.markdown("<p class='hidden-markdown'</p>", unsafe_allow_html=True)
        else:
            # Person ausgewählt, aber keine Daten vorhanden
            st.warning("Die Daten zur ausgewählten Person konnten nicht gefunden werden. Möglicherweise wurde die Person gelöscht.")
            st.session_state['person_select_box'] = "" # Selectbox zurücksetzen
            st.session_state['show_delete_confirmation'] = False
            st.session_state['show_person_details'] = False
            


    # Lösch-Button und Bestätigungsdialog
    if selected_person_name_data_tab and not st.session_state['show_new_person_form']:
        if not st.session_state.get('show_delete_confirmation', False):
            
            person_data_for_delete = Person.find_person_data_by_name(selected_person_name_data_tab)
            if person_data_for_delete:
                st.button(
                    "Löschen",
                    key="delete_person_button_main",
                    on_click=prepare_delete_callback,
                    args=(person_data_for_delete['id'], selected_person_name_data_tab)
                )
            else:
                
                st.session_state['person_select_box'] = "" 
                st.session_state['show_person_details'] = False


        # Bestätigungsdialog anzeigen
        if st.session_state.get('show_delete_confirmation', False) and \
           st.session_state.get('confirm_delete_id') is not None: 
            
            # Stelle sicher, dass der Name für die Bestätigung noch aktuell ist
            display_name = st.session_state.get('confirm_delete_name', "diese Person")

            st.warning(f"Sind Sie sicher, dass Sie **{display_name}** unwiderruflich löschen möchten?")
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                st.button(
                    "Ja, endgültig löschen",
                    key="confirm_delete_yes_button",
                    on_click=execute_delete_callback,
                    args=(st.session_state['confirm_delete_id'], st.session_state['confirm_delete_name'])
                )

            with col_confirm2:
                st.button("Abbrechen", key="confirm_delete_no_button", on_click=cancel_delete_callback)


    # Anfangsnachricht, wenn nichts ausgewählt ist und kein anderer Zustand aktiv ist
    if not st.session_state['person_select_box'] and \
       not st.session_state['show_new_person_form'] and \
       not st.session_state['person_added_message'] and \
       not st.session_state['person_deleted_message'] and \
       not st.session_state['show_delete_confirmation'] and \
       not st.session_state['show_person_details']:
        st.info("Bitte wählen Sie eine Person aus oder legen Sie eine neue an.")

    if st.session_state.get('show_edit_person_form', False) and person_data:

        st.subheader("Person bearbeiten")

        with st.form("bearbeite_person_formular"):
            firstname = st.text_input("Vorname", value=person_data["firstname"])
            lastname = st.text_input("Nachname", value=person_data["lastname"])
            birth_date = st.date_input("Geburtsdatum", value=pd.to_datetime(person_data["date_of_birth"]))
            gender = st.selectbox("Geschlecht", ["male", "female"], index=["male", "female"].index(person_data.get("gender", "male")))
            address = st.text_input("Adresse", value=person_data.get("address", ""))
            phone_number = st.text_input("Telefonnummer", value=person_data.get("phone_number", ""))

            st.markdown("### Optional: Neue Dateien hochladen")
            picture_file = st.file_uploader("Neues Profilbild hochladen", type=["jpg", "jpeg", "png"])
            ekg_file = st.file_uploader("Neuer EKG-Test (TXT/CSV)", type=["txt", "csv"])
            ftp_file = st.file_uploader("Neuer FTP-Test (FIT/CSV)", type=["fit", "csv"])

            submitted = st.form_submit_button("Änderungen speichern")

        if submitted:
            # Dateiordner vorbereiten
            os.makedirs("data/files", exist_ok=True)
            os.makedirs("data/pictures", exist_ok=True)

            # Update Felder
            person_data["firstname"] = firstname.strip()
            person_data["lastname"] = lastname.strip()
            person_data["date_of_birth"] = birth_date.strftime("%Y-%m-%d")
            person_data["gender"] = gender
            person_data["address"] = address.strip()
            person_data["phone_number"] = phone_number.strip()

            # Bild speichern
            if picture_file:
                profile_picture_path = f"data/pictures/profile_{person_data['id']}_{picture_file.name}"
                with open(profile_picture_path, "wb") as f:
                    f.write(picture_file.getbuffer())
                person_data["picture_path"] = profile_picture_path

            # Neuen EKG-Test hinzufügen
            if ekg_file:
                ekg_file_path = f"data/files/ruhe_ekg_{person_data['id']}_{ekg_file.name}"
                with open(ekg_file_path, "wb") as f:
                    f.write(ekg_file.getbuffer())
                existing_ekg_ids = [test["id"] for p in persons_list for test in p.get("ekg_tests", [])]
                new_ekg_id = max(existing_ekg_ids + [0]) + 1
                person_data.setdefault("ekg_tests", []).append({
                    "id": new_ekg_id,
                    "date": date.today().isoformat(),
                    "result_link": ekg_file_path
                })

            # Neuen FTP-Test hinzufügen
            if ftp_file:
                ftp_file_path = f"data/files/ftp_test_{person_data['id']}_{ftp_file.name}"
                with open(ftp_file_path, "wb") as f:
                    f.write(ftp_file.getbuffer())
                existing_ftp_ids = [test["id"] for p in persons_list for test in p.get("ftp_tests", [])]
                new_ftp_id = max(existing_ftp_ids + [0]) + 1
                person_data.setdefault("ftp_tests", []).append({
                    "id": new_ftp_id,
                    "date": date.today().isoformat(),
                    "result_link": ftp_file_path
                })

            # Speichern
            for i, p in enumerate(persons_list):
                if p["id"] == person_data["id"]:
                    persons_list[i] = person_data
                    break
            Person.save_person_data(persons_list)

            st.success("Personendaten erfolgreich aktualisiert.")
            st.session_state['show_edit_person_form'] = False
            st.rerun()

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
                            st.metric("Herzfrequenz (bpm)", hr)
                        else:
                            st.warning("Nicht genügend Peaks zur Herzfrequenz-Berechnung gefunden.")

                        # Plot erstellen und anzeigen
                        # Das Figure-Objekt von plot_time_series() abfangen und an st.pyplot übergeben
                        df = ekg.df

                        if df is not None and not df.empty:
                            y_column = None
                            for col in df.columns:
                                if col.lower() in ["value", "amplitude", "signal", "volt", "messwerte in mv","spannung","wert"]:
                                    y_column = col
                                    break

                            if y_column is None:
                                st.error("Keine geeignete Spalte für EKG-Daten gefunden (z. B. 'value', 'signal', 'amplitude').")
                            else:
                                fig = go.Figure()

                                fig.add_trace(go.Scatter(
                                    x=df.index,
                                    y=df[y_column],
                                    mode="lines",
                                    name="EKG-Signal",
                                    hovertemplate="Zeit: %{x}<br>Wert: %{y} mV<extra></extra>"
                                ))
                                # Peaks berechnen und anzeigen
                                try:
                                    respacing_factor = 5  # oder z. B. 1 für maximale Genauigkeit
                                    peaks = ekg.find_peaks(threshold=threshold, respacing_factor=respacing_factor)
                                    peak_df = df.iloc[peaks]

                                    fig.add_trace(go.Scatter(
                                        x=peak_df.index,
                                        y=peak_df[y_column],
                                        mode="markers",
                                        name="Peaks",
                                        marker=dict(color="red", size=8),
                                        hovertemplate="Peak<br>Zeit: %{x}<br>Wert: %{y} mV<extra></extra>"
                                    ))
                                except Exception as e:
                                    st.warning(f"Fehler beim Ermitteln der Peaks: {e}")


                                fig.update_layout(
                                    title="Ruhe-EKG Verlauf",
                                    xaxis_title="Zeit",
                                    yaxis_title="Amplitude",
                                    hovermode="x unified",
                                    template="plotly_white"
                                )

                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Keine EKG-Daten zum Anzeigen verfügbar.")

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


                        st.write(f"### FTP-Test: ID {ftp.id}, Datum: {ftp.date}")
                        st.write(f"Person: {ftp.person_firstname} {ftp.person_lastname}")

                        df = ftp.df
                        if not df.empty:
                            st.write("### Zusammenfassung des Tests")
                            dauer = df.index[-1] - df.index[0]
                            dauer_min = round(dauer.total_seconds() / 60, 1)
                            mean_hr = round(df["heart_rate"].mean(), 1) if "heart_rate" in df else "?"
                            max_power = df["power"].max() if "power" in df else "?"
                            max_hr = df["heart_rate"].max() if "heart_rate" in df else "?"

                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Gesamtdauer", f"{dauer_min} Minuten")
                                st.metric("Maximale Leistung", f"{max_power} Watt")
                            with col2:
                                st.metric("Maximale Herzfrequenz", f"{max_hr} bpm")
                                st.metric("Ø Herzfrequenz", f"{mean_hr} bpm")
                            
                            
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
                            fig = go.Figure()

                            if show_hr and "heart_rate" in df.columns:
                                fig.add_trace(go.Scatter(
                                    x=df["minuten"],
                                    y=df["heart_rate"],
                                    mode="lines",
                                    name="Herzfrequenz",
                                    hovertemplate='Zeit: %{x:.1f} Min<br>Herzfrequenz: %{y} bpm<extra></extra>'
                                ))

                            if show_power and "power" in df.columns:
                                fig.add_trace(go.Scatter(
                                    x=df["minuten"],
                                    y=df["power"],
                                    mode="lines",
                                    name="Leistung",
                                    hovertemplate='Zeit: %{x:.1f} Min<br>Leistung: %{y} W<extra></extra>'
                                ))

                            if show_cadence and "cadence" in df.columns:
                                fig.add_trace(go.Scatter(
                                    x=df["minuten"],
                                    y=df["cadence"],
                                    mode="lines",
                                    name="Trittfrequenz",
                                    hovertemplate='Zeit: %{x:.1f} Min<br>TF: %{y} rpm<extra></extra>'
                                ))

                            fig.update_layout(
                                title="Verlauf: Herzfrequenz, Leistung, Trittfrequenz",
                                xaxis_title="Zeit (Minuten)",
                                yaxis_title="Wert",
                                hovermode="x unified",
                                template="plotly_white"
                            )

                            st.plotly_chart(fig, use_container_width=True)



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
            ftp_tests = person_data_for_zones.get("ftp_tests", [])
            if ftp_tests:
                # Nimm den neuesten FTP-Test (höchste ID)
                ftp_test_sorted = sorted(ftp_tests, key=lambda x: x['id'], reverse=True)[0]
                ftp_path = ftp_test_sorted.get("result_link")
                if ftp_path:
                    try:
                        ftp_test_obj = FTP_Test(ftp_path)
                        df = ftp_test_obj.df
                        if not df.empty and "heart_rate" in df.columns:
                            max_hr_for_zones = df["heart_rate"].max()
                    except Exception as e:
                        st.warning(f"Fehler beim Auslesen des FTP-Tests: {e}")

            if max_hr_for_zones is None:
                st.warning(f"Keine maximale Herzfrequenz für **{selected_person_name}** verfügbar. Bitte FTP-Test-Wert eingeben oder Geburtsdatum/Geschlecht prüfen.")

    # Aktualisiere den HF-Zonen DataFrame
    if max_hr_for_zones is not None:
        hf_zones_data = {
            "Zone": ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"],
            "Prozentsatz der MHF": ["50-60%", "60-70%", "70-80%", "80-90%", "90-100%"],
            "Berechnete Zonen (bpm)": [] 
        }

        # Berechne die HF-Werte für jede Zone
        ranges = [(0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 0.90), (0.90, 1.00)]
        for lower_bound, upper_bound in ranges:
            min_hr = round(max_hr_for_zones * lower_bound)
            max_hr = round(max_hr_for_zones * upper_bound)
            hf_zones_data["Berechnete Zonen (bpm)"].append(f"{min_hr}-{max_hr}") 

        st.session_state['hf_zones_df'] = pd.DataFrame(hf_zones_data)
        st.info(f"Die Herzfrequenz-Zonen basieren auf der maximalen HF aus dem letzten FTP-Test (**{round(max_hr_for_zones)} bpm**) von **{selected_person_name}**.")

    else:
        # Standard-Werte, wenn keine Person ausgewählt ist oder MHF nicht berechnet werden kann
        st.info("Bitte wählen Sie eine Person im Tab 'Daten' aus und geben Sie ggf. die maximale Herzfrequenz an, um personalisierte HF-Zonen anzuzeigen.")
        st.session_state['hf_zones_df'] = pd.DataFrame({
            "Zone": ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5"],
            "Prozentsatz der MHF": ["50-60%", "60-70%", "70-80%", "80-90%", "90-100%"],
            "Berechnete Zonen (bpm)": ["", "", "", "", ""] 
        })


    # Funktion zum Stylen des DataFrames (für Zeilenfarben)
    def highlight_zones(row): 
        colors = {
            "Zone 1": '#e6ffe6', 
            "Zone 2": '#cce6ff', 
            "Zone 3": '#ffffcc', 
            "Zone 4": '#ffcccc', 
            "Zone 5": '#ff9999'  
        }
        zone_name = row['Zone'] 
        color = colors.get(zone_name, '') 

        return [f'background-color: {color};color: black' for _ in row.index]


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
        height=300,         # Feste Höhe für die Tabelle
        use_container_width=True, # Passt sich der Container-Breite an
        
        column_order=("Tag", "Übung", "Dauer (Min.)", "Intensität"), 
        column_config={
            "Tag": st.column_config.Column(
                "Tag",
                help="Der Wochentag",
                width="small",
                disabled=True 
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
                options=["Zone 1", "Zone 2", "Zone 3", "Zone 4","Zone 5", ""], 
                required=False,
                width="small"
            )
            
        }
    )

    # Speichern des bearbeiteten Trainings-DataFrames 
    st.session_state['training_plan_df'] = edited_df_training_plan


    # Funktion zum Erzeugen des PDF-Berichts
    def create_training_report_pdf(person_name, hf_zones_df, training_plan_df, ekg_summary, ftp_summary, person_data, ekg_plot_path=None, ftp_plot_path=None):


        pdf = FPDF()
        pdf.add_page()
        # Setze einen Font, der Umlaute unterstützt (z.B. DejaVuSans-Bold oder Arial, wenn es kein Problem gibt)
        # FPDF benötigt TTF-Dateien, die in das Skript eingebettet oder vorher registriert werden müssen
        # Für einfache Umlaute ohne spezielle Font-Dateien reicht latin-1 encoding bei der Ausgabe,
        # aber Arial muss in der FPDF-Installation verfügbar sein (ist es standardmäßig).
        pdf.set_font("Arial", size=12)

        # Titel
        pdf.cell(200, 10, txt=f"Trainingsbericht für {person_name}", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Personendaten:", ln=True, align="L")
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 8, txt=f"Name: {person_data.get('firstname', '')} {person_data.get('lastname', '')}", ln=True)
        pdf.cell(200, 8, txt=f"Geburtsdatum: {person_data.get('date_of_birth', '')}", ln=True)
        pdf.cell(200, 8, txt=f"Adresse: {person_data.get('address', '')}", ln=True)
        pdf.cell(200, 8, txt=f"Telefon: {person_data.get('phone_number', '')}", ln=True)
        pdf.ln(10)

        # HF-Zonen
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Herzfrequenz-Zonen:", ln=True, align="L")
        pdf.set_font("Arial", size=10)
        pdf.ln(2)

        # Tabelle der HF-Zonen
        # Header
        pdf.set_fill_color(200, 220, 255) # Light blue background for header
        
        # Passe die Spaltenbreiten dynamisch an die Anzahl der Spalten an
        left_margin = pdf.l_margin  # Standard: 10 mm
        right_margin = pdf.r_margin  # meist ebenfalls 10 mm
        usable_width = pdf.w - left_margin - right_margin

        hf_col_width = usable_width / len(hf_zones_df.columns)
        for col in hf_zones_df.columns:
            pdf.cell(hf_col_width, 7, col, 1, 0, 'C', 1)
        pdf.ln()

        # Data rows
        for index, row in hf_zones_df.iterrows():
            for col in hf_zones_df.columns:
                pdf.cell(hf_col_width, 7, str(row[col]), 1, 0, 'C')
            pdf.ln()
        pdf.ln(10)

        # Trainingsplan
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Trainingsplan:", ln=True, align="L")
        pdf.set_font("Arial", size=10)
        pdf.ln(2)

        # Tabelle des Trainingsplans
        # Header (Angepasste Spaltenbreiten - 'Notizen' Spalte entfernt)
        # Passen Sie die Breiten entsprechend an die verbleibenden 4 Spalten an
        # Tag, Übung, Dauer (Min.), Intensität
        headers_training = training_plan_df.columns.tolist()

        # Verfügbare Breite korrekt berechnen
        usable_width = pdf.w - pdf.l_margin - pdf.r_margin

        # Gleichmäßige Spaltenbreiten
        col_widths_training = [usable_width / len(headers_training)] * len(headers_training)


        pdf.set_fill_color(200, 220, 255) # Light blue background for header
        
        for i, header in enumerate(headers_training):
            pdf.cell(col_widths_training[i], 7, header, 1, 0, 'C', 1)
        pdf.ln()

        # Data rows
        for index, row in training_plan_df.iterrows():
            for i, col_name in enumerate(headers_training):
                pdf.cell(col_widths_training[i], 7, str(row[col_name]), 1, 0, 'L') # 'L' für linksbündig
            pdf.ln()

        pdf.add_page()

        # Zusammenfassung EKG
        if ekg_summary:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Auswertung Ruhe-EKG:", ln=True, align="L")
            pdf.set_font("Arial", size=10)
            for k, v in ekg_summary.items():
                pdf.cell(200, 8, txt=f"{k}: {v}", ln=True)
            pdf.ln(5)

            # EKG-Plot direkt darunter
            if ekg_plot_path and os.path.exists(ekg_plot_path):
                pdf.image(ekg_plot_path, x=10, w=180)
                pdf.ln(10)

        # Zusammenfassung FTP
        if ftp_summary:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Auswertung FTP-Test:", ln=True, align="L")
            pdf.set_font("Arial", size=10)
            for k, v in ftp_summary.items():
                pdf.cell(200, 8, txt=f"{k}: {v}", ln=True)
            pdf.ln(5)

            # FTP-Plot direkt darunter
            if ftp_plot_path and os.path.exists(ftp_plot_path):
                pdf.image(ftp_plot_path, x=10, w=180)
                pdf.ln(10)

       

        # WICHTIG: Die Ausgabe sollte in 'latin-1' erfolgen, wenn Umlaute direkt ohne spezielle Font-Dateien verwendet werden
        # oder 'utf-8' wenn der FPDF Font diese unterstützt und zuvor geladen wurde (z.B. DejaVuSans)
        return bytes(pdf.output(dest='S'))
    



    # Export-Button für PDF
    if st.button("PDF exportieren"):
        if selected_person_name:
            person_data = Person.find_person_data_by_name(selected_person_name)
            ftp_summary = {}
            ekg_summary = {}

            # FTP-Auswertung laden
            ftp_tests = person_data.get("ftp_tests", [])
            if ftp_tests:
                latest_ftp = sorted(ftp_tests, key=lambda x: x["id"], reverse=True)[0]
                ftp_obj = FTP_Test(file_path=latest_ftp["result_link"])
                ftp_summary = ftp_obj.get_summary()

            # EKG-Auswertung laden
            ekg_tests = person_data.get("ekg_tests", [])
            if ekg_tests:
                latest_ekg = sorted(ekg_tests, key=lambda x: x["id"], reverse=True)[0]
                ekg_obj = EKGdata.load_by_id(latest_ekg["id"], persons_list)
                threshold = ekg_obj.auto_threshold()
                bpm = ekg_obj.estimate_hr(threshold)
                if bpm:
                    ekg_summary = {"Herzfrequenz": f"{bpm} bpm"}
            ekg_plot_path = None
            ftp_plot_path = None

            if ekg_tests:
                latest_ekg = sorted(ekg_tests, key=lambda x: x["id"], reverse=True)[0]
                ekg_obj = EKGdata.load_by_id(latest_ekg["id"], persons_list)
                threshold = ekg_obj.auto_threshold()
                bpm = ekg_obj.estimate_hr(threshold)
                if bpm:
                    ekg_summary = {"Geschätzte Herzfrequenz": f"{bpm} bpm"}

                # EKG-Plot speichern
                fig = ekg_obj.plot_time_series(threshold=threshold)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                    fig.savefig(tmpfile.name)
                    ekg_plot_path = tmpfile.name
                    plt.close(fig)  # Speicher freigeben

            if ftp_tests:
                latest_ftp = sorted(ftp_tests, key=lambda x: x["id"], reverse=True)[0]
                ftp_obj = FTP_Test(file_path=latest_ftp["result_link"])
                ftp_summary = ftp_obj.get_summary()

                # FTP-Plot speichern
                df = ftp_obj.get_dataframe()
                if not df.empty:
                    start_time = df.index[0]
                    df["minuten"] = (df.index - start_time).total_seconds() / 60
                    fig, ax = plt.subplots(figsize=(10, 4))
                    if "heart_rate" in df:
                        ax.plot(df["minuten"], df["heart_rate"], label="Herzfrequenz", alpha=0.8)
                    if "power" in df:
                        ax.plot(df["minuten"], df["power"], label="Leistung", alpha=0.8)
                    if "cadence" in df:
                        ax.plot(df["minuten"], df["cadence"], label="Trittfrequenz", alpha=0.8)
                    ax.set_xlabel("Zeit (Minuten)")
                    ax.set_ylabel("Wert")
                    ax.legend()
                    ax.set_title("FTP-Test Verlauf")
                    plt.tight_layout()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                        fig.savefig(tmpfile.name)
                        ftp_plot_path = tmpfile.name
                        plt.close(fig)

            pdf_output = create_training_report_pdf(
                selected_person_name,
                st.session_state['hf_zones_df'],
                st.session_state['training_plan_df'],
                ekg_summary,
                ftp_summary,
                person_data,
                ekg_plot_path=ekg_plot_path,
                ftp_plot_path=ftp_plot_path
            )

            st.download_button(
                label="PDF herunterladen",
                data=pdf_output,
                file_name=f"Trainingsplan_{selected_person_name.replace(' ', '_')}_{date.today().isoformat()}.pdf",
                mime="application/pdf"
            )
            st.success("PDF-Bericht erfolgreich erstellt. Klicken Sie auf 'PDF herunterladen'.")
        else:
            st.warning("Bitte wählen Sie eine Person aus, um den Trainingsplan als PDF zu exportieren.")






