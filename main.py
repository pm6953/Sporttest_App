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
from fpdf import FPDF
import io

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
if 'just_added_person_name' not in st.session_state:
    st.session_state['just_added_person_name'] = ""

# Session State Variablen für PDF-Inhalte und Grafik-Buffer aus allen Tabs
if 'hf_graphic_buffer' not in st.session_state:
    st.session_state['hf_graphic_buffer'] = None
if 'ekg_graphic_buffer' not in st.session_state:
    st.session_state['ekg_graphic_buffer'] = None
if 'current_ekg_data' not in st.session_state: # Speichert den DataFrame der EKG-Daten
    st.session_state['current_ekg_data'] = None
if 'ftp_graphic_buffer' not in st.session_state:
    st.session_state['ftp_graphic_buffer'] = None
if 'current_ftp_data' not in st.session_state: # Speichert den DataFrame der FTP-Daten
    st.session_state['current_ftp_data'] = None
if 'selected_person_full_data' not in st.session_state: # Speichert die vollen Personendaten
    st.session_state['selected_person_full_data'] = None

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
        # Lade die vollständigen Daten der ausgewählten Person
        st.session_state['selected_person_full_data'] = Person.find_person_data_by_name(st.session_state['person_select_box'])
    else:
        st.session_state['show_person_details'] = False
        st.session_state['show_new_person_form'] = False
        st.session_state['show_delete_confirmation'] = False
        st.session_state['person_deleted_message'] = False
        st.session_state['person_added_message'] = False
        st.session_state['selected_person_full_data'] = None 

    st.session_state['missing_optional_fields_message'] = "" # Meldung zurücksetzen
    st.session_state['just_added_person_name'] = "" # Wichtig: reset this
    st.session_state['hf_graphic_buffer'] = None
    st.session_state['ekg_graphic_buffer'] = None
    st.session_state['current_ekg_data'] = None
    st.session_state['ftp_graphic_buffer'] = None
    st.session_state['current_ftp_data'] = None

# Callback: Nach erfolgreichem Hinzufügen einer Person
def on_person_add_success_indicator(firstname, lastname, missing_fields_message=""):
    st.session_state['person_added_message'] = True
    st.session_state['last_added_person_name'] = f"{firstname} {lastname}"
    st.session_state['show_new_person_form'] = False
    st.session_state['show_person_details'] = True
    st.session_state['missing_optional_fields_message'] = missing_fields_message 
    st.session_state['just_added_person_name'] = f"{firstname} {lastname}" # <-- Wichtig: Setzt den Namen hier!
    # FÜR PDF: Clear aller PDF-bezogenen Session States
    st.session_state['hf_graphic_buffer'] = None
    st.session_state['ekg_graphic_buffer'] = None
    st.session_state['current_ekg_data'] = None
    st.session_state['ftp_graphic_buffer'] = None
    st.session_state['current_ftp_data'] = None
    # 'selected_person_full_data' wird nach experimental_rerun gesetzt

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
    st.write("### Person auswählen:")
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
            "_", 
            options=[""] + person_names,
            index=default_index, 
            key="person_select_box",
            label_visibility="hidden", # Versteckt das Label
            on_change=on_person_select_change # Hinzugefügter Callback
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
            birth_date = st.date_input("Geburtsdatum", value=date.today(), key="new_person_birthdate")
            gender = st.selectbox("Geschlecht", ["male", "female"], key="new_person_gender")
            address = st.text_input("Adresse", key="new_person_address") 
            phone_number = st.text_input("Telefonnummer", key="new_person_phone_number")
            st.markdown("### Optional: Dateien hochladen")
            picture_file = st.file_uploader("Profilbild hochladen ", type=["jpg", "jpeg", "png"], key="new_person_picture_file")
            ruhe_ekg_file = st.file_uploader("Ruhe-EKG PDF", type=["pdf"], key="ruhe_ekg_upload")
            ftp_test_file = st.file_uploader("FTP-Test PDF", type=["pdf"], key="ftp_test_upload")
            
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
                        "ftp_test_file": ftp_file_path
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

                        # Speichern des EKG-DataFrames im Session State
                        # `ekg.df` sollte das DataFrame des geladenen EKG-Tests sein
                        st.session_state['current_ekg_data'] = ekg.df 

                        # Speichern des EKG-Grafik-Buffers im Session State
                        # fig_to_display ist die Matplotlib-Figur, die du gerade erstellt hast
                        ekg_buffer = io.BytesIO()
                        fig_to_display.savefig(ekg_buffer, format='png') # Speichert die Grafik als PNG
                        st.session_state['ekg_graphic_buffer'] = ekg_buffer

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

                            # Speichern des FTP-DataFrames im Session State
                            st.session_state['current_ftp_data'] = df

                            # Speichern des FTP-Grafik-Buffers im Session State
                            ftp_buffer = io.BytesIO()
                            fig.savefig(ftp_buffer, format='png') # Speichert die Grafik als PNG
                            st.session_state['ftp_graphic_buffer'] = ftp_buffer
                            plt.close(fig) # Schließt die Matplotlib-Figur

                        else:
                            st.warning("Keine darstellbaren Daten im FTP-Test gefunden.")
                            st.session_state['current_ftp_data'] = None
                            st.session_state['ftp_graphic_buffer'] = None

                    except Exception as e:
                        st.error(f"Fehler beim Laden des FTP-Tests: {e}")
                        # Bei Fehler, Session State zurücksetzen
                        st.session_state['current_ftp_data'] = None
                        st.session_state['ftp_graphic_buffer'] = None
            else:
                st.info("Für die ausgewählte Person sind keine FTP-Tests vorhanden.")
                # Wenn keine Tests, auch Session State zurücksetzen
                st.session_state['current_ftp_data'] = None
                st.session_state['ftp_graphic_buffer'] = None
        else:
            st.warning("Die Daten zur ausgewählten Person konnten nicht gefunden werden. Bitte überprüfen Sie Ihre Auswahl.")
            st.session_state['current_ftp_data'] = None
            st.session_state['ftp_graphic_buffer'] = None
    else:
        st.info("Bitte wählen Sie zuerst eine Person im Tab 'Daten' aus, um FTP-Tests anzuzeigen.")
        st.session_state['current_ftp_data'] = None
        st.session_state['ftp_graphic_buffer'] = None # Initialisiere mit None, wenn keine Person ausgewählt

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
            "Berechnete Zonen (bpm)": [] 
        }

        # Berechne die HF-Werte für jede Zone
        ranges = [(0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 0.90), (0.90, 1.00)]
        for lower_bound, upper_bound in ranges:
            min_hr = round(max_hr_for_zones * lower_bound)
            max_hr = round(max_hr_for_zones * upper_bound)
            hf_zones_data["Berechnete Zonen (bpm)"].append(f"{min_hr}-{max_hr}") 

        st.session_state['hf_zones_df'] = pd.DataFrame(hf_zones_data)
        st.info(f"Die Herzfrequenz-Zonen basieren auf einer maximalen Herzfrequenz von **{round(max_hr_for_zones)} bpm** für **{selected_person_name}**.")
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
        height=300,         # Feste Höhe für die Tabelle
        use_container_width=True, # Passt sich der Container-Breite an
        # 'Notizen' aus column_order entfernt
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
    def create_training_report_pdf(person_data, hf_zones_df, training_plan_df,
                                     hf_graphic_buffer_data,
                                     ekg_df_data, ekg_graphic_buffer_data,
                                     ftp_df_data, ftp_graphic_buffer_data):
                                     
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_left_margin(10)  # Setzt den linken Rand auf 10mm
        pdf.set_right_margin(10) # Setzt den rechten Rand auf 10mm
        pdf.set_font("Arial", size=12)
        available_width = pdf.w - pdf.l_margin - pdf.r_margin 
        # Titel des Berichts
        pdf.cell(0, 10, txt=f"Sporttest-Bericht für {person_data['firstname']} {person_data['lastname']}", ln=True, align="C")
        pdf.ln(10)
         
        # --- 1. Personen-Details (aus Tab 'Daten') ---
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt="1. Personen-Details:", ln=True, align="L")
        pdf.set_font("Arial", size=10)
        pdf.ln(2)
        pdf.multi_cell(0, 7, f"Name: {person_data['firstname']} {person_data['lastname']}")
        
        pdf.set_x(pdf.l_margin)

        display_birthdate_pdf = "Nicht angegeben"
        if person_data.get('birthdate'):
            try:
                display_birthdate_pdf = date.fromisoformat(person_data['birthdate']).strftime("%d.%m.%Y")
            except (TypeError, ValueError):
                display_birthdate_pdf = "Ungültiges Datum im Datensatz"

               
        #Geburtsdatum
        pdf.multi_cell(0, 7, f"Geburtsdatum: {display_birthdate_pdf}")
        pdf.set_x(pdf.l_margin)

        #Geschlecht
        pdf.multi_cell(0, 7, f"Geschlecht: {person_data['gender'] if person_data['gender'] else 'Nicht angegeben'}")
        pdf.set_x(pdf.l_margin)

        #FTP-Wert
        ftp_value_for_pdf = person_data.get('ftp_value')
        if ftp_value_for_pdf is not None:
            pdf.multi_cell(0, 7, f"Aktueller FTP-Wert: {ftp_value_for_pdf} Watt")
        else:
            pdf.multi_cell(0, 7, "Aktueller FTP-Wert: Nicht angegeben")
        pdf.set_x(pdf.l_margin)
        pdf.ln(10)
        


        # --- 2. Herzfrequenz-Zonen ---
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt="2. Herzfrequenz-Zonen:", ln=True, align="L")
        pdf.set_font("Arial", size=10)
        pdf.ln(2)

        # Herzfrequenz-Grafik
        if hf_graphic_buffer_data:
            hf_graphic_buffer_data.seek(0) # WICHTIG: Buffer auf 0 zurücksetzen, bevor gelesen wird
            pdf.image(hf_graphic_buffer_data, x=10, w=180, h=0)
            pdf.ln()
            pdf.set_y(pdf.get_y() + 10)
        else:
            pdf.multi_cell(0, 7, "Keine Herzfrequenz-Zonen Grafik verfügbar.")
            pdf.ln(10)


        # Herzfrequenz-Tabelle
        pdf.set_fill_color(200, 220, 255)
        hf_col_width_zone = 40
        hf_col_width_percent = 60
        hf_col_width_bpm = 80
        hf_widths = [hf_col_width_zone, hf_col_width_percent, hf_col_width_bpm]

        headers_hf = hf_zones_df.columns.tolist()
        for i, col in enumerate(headers_hf):
            pdf.cell(hf_widths[i], 7, col, 1, 0, 'C', 1)
        pdf.ln()

        for index, row in hf_zones_df.iterrows():
            pdf.cell(hf_widths[0], 7, str(row['Zone']), 1, 0, 'C')
            pdf.cell(hf_widths[1], 7, str(row['Prozentsatz der MHF']), 1, 0, 'C')
            pdf.cell(hf_widths[2], 7, str(row['Berechnete Zonen (bpm)']), 1, 0, 'C')
            pdf.ln()
        pdf.ln(10)


        # --- 3. EKG-Test Daten (aus Tab 'Tests') ---
        # Füge nur hinzu, wenn Daten vorhanden sind
        if ekg_df_data is not None and not ekg_df_data.empty and ekg_graphic_buffer_data is not None:
            pdf.add_page()
            pdf.set_xy(pdf.l_margin, pdf.t_margin)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt="3. EKG-Testdaten:", ln=True, align="L")
            pdf.set_font("Arial", size=10)
            pdf.ln(2)

            # EKG-Grafik einbetten
            ekg_graphic_buffer_data.seek(0) 
            img_width = 180
            img_height = 0
            if ekg_graphic_buffer_data is not None:
                ekg_graphic_buffer_data.seek(0, io.SEEK_END)
                size = ekg_graphic_buffer_data.tell()
                ekg_graphic_buffer_data.seek(0)

                if size == 0:
                    pdf.multi_cell(0, 7, "Hinweis: EKG-Bild ist leer und kann nicht eingefügt werden.")
                else:
                    try:
                        pdf.image(ekg_graphic_buffer_data, x=10, w=img_width, h=img_height)
                    except Exception as e:
                        pdf.multi_cell(0, 7, f"Fehler beim Einfügen des EKG-Bilds: {e}")
            pdf.ln()
            pdf.set_y(pdf.get_y() + 10) 

            # EKG-Daten Tabelle (nur die ersten paar Zeilen zur Übersicht)
            #pdf.set_x(pdf.l_margin)
            pdf.multi_cell(available_width - 1, 7, "Erste Zeilen der EKG-Daten:")
            ekg_display_df = ekg_df_data.head(5).copy()

            columns_to_display_ekg = ['Timestamp', 'HeartRate', 'Power', 'Cadence', 'Speed'] # Reihenfolge angepasst
            ekg_display_df = ekg_display_df[[col for col in columns_to_display_ekg if col in ekg_display_df.columns]]

            ekg_header_widths = []
            if not ekg_display_df.empty:
                for col in ekg_display_df.columns:
                    ekg_header_widths.append(min(pdf.get_string_width(str(col)) + 6, 40)) # Max 40, dynamisch an Text

                total_width = sum(ekg_header_widths)
                page_width = pdf.w - 20
                if total_width > page_width and total_width > 0:
                    scale_factor = page_width / total_width
                    ekg_header_widths = [w * scale_factor for w in ekg_header_widths]

            if ekg_header_widths and not ekg_display_df.empty:
                pdf.set_fill_color(200, 220, 255)
                for i, col in enumerate(ekg_display_df.columns):
                    pdf.cell(ekg_header_widths[i], 7, col, 1, 0, 'C', 1)
                pdf.ln()

                for index, row in ekg_display_df.iterrows():
                    for i, col_name in enumerate(ekg_display_df.columns):
                        cell_content = ""
                        if pd.notna(row[col_name]):
                            if col_name == 'Timestamp':
                                try:
                                    cell_content = pd.to_datetime(row[col_name]).strftime('%H:%M:%S')
                                except:
                                    cell_content = str(row[col_name])
                            else:
                                cell_content = str(round(row[col_name], 2))
                        pdf.cell(ekg_header_widths[i], 7, cell_content, 1, 0, 'L')
                    pdf.ln()
            else:
                pdf.multi_cell(0, 7, "Keine EKG-Daten zur Anzeige verfügbar.")
            pdf.ln(10)
        else:
            pdf.add_page()
            pdf.set_xy(pdf.l_margin, pdf.t_margin)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt="3. EKG-Testdaten:", ln=True, align="L")
            pdf.set_font("Arial", size=10)
            pdf.ln(2)
            #pdf.set_x(pdf.l_margin)
            pdf.multi_cell(available_width - 1, 7, "Keine EKG-Testdaten oder zugehörige Grafik für diesen Bericht verfügbar. Bitte laden Sie eine EKG-Datei im 'Tests'-Tab hoch.")
            pdf.ln(10)


        # --- 4. FTP-Test Daten (aus Tab 'FTP-Test') ---
        if ftp_df_data is not None and not ftp_df_data.empty and ftp_graphic_buffer_data is not None:
            pdf.add_page()
            pdf.set_xy(pdf.l_margin, pdf.t_margin)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt="4. FTP-Testdaten:", ln=True, align="L")
            pdf.set_font("Arial", size=10)
            pdf.ln(2)

            # FTP-Grafik einbetten
            ftp_graphic_buffer_data.seek(0) # WICHTIG: Buffer auf 0 zurücksetzen
            if ftp_graphic_buffer_data is not None:
                ftp_graphic_buffer_data.seek(0, io.SEEK_END)
                size = ftp_graphic_buffer_data.tell()
                ftp_graphic_buffer_data.seek(0)

                if size == 0:
                    pdf.multi_cell(0, 7, "Hinweis: FTP-Bild ist leer und kann nicht eingefügt werden.")
                else:
                    try:
                        pdf.image(ftp_graphic_buffer_data, x=10, w=180, h=0)
                    except Exception as e:
                        pdf.multi_cell(0, 7, f"Fehler beim Einfügen des FTP-Bilds: {e}")
            pdf.ln()
            pdf.set_y(pdf.get_y() + 10)

            # FTP-Daten Tabelle (nur die ersten paar Zeilen zur Übersicht)
            #pdf.set_x(pdf.l_margin)
            pdf.multi_cell(available_width - 1, 7, "Erste Zeilen der FTP-Daten:")
            ftp_display_df = ftp_df_data.head(5).copy()

            columns_to_display_ftp = ['Timestamp', 'Power', 'HeartRate', 'Cadence', 'Speed'] # Reihenfolge angepasst
            ftp_display_df = ftp_display_df[[col for col in columns_to_display_ftp if col in ftp_display_df.columns]]

            ftp_header_widths = []
            if not ftp_display_df.empty:
                for col in ftp_display_df.columns:
                    ftp_header_widths.append(min(pdf.get_string_width(str(col)) + 6, 40))

                total_width = sum(ftp_header_widths)
                page_width = pdf.w - 20
                if total_width > page_width and total_width > 0:
                    scale_factor = page_width / total_width
                    ftp_header_widths = [w * scale_factor for w in ftp_header_widths]

            if ftp_header_widths and not ftp_display_df.empty:
                pdf.set_fill_color(200, 220, 255)
                for i, col in enumerate(ftp_display_df.columns):
                    pdf.cell(ftp_header_widths[i], 7, col, 1, 0, 'C', 1)
                pdf.ln()

                for index, row in ftp_display_df.iterrows():
                    for i, col_name in enumerate(ftp_display_df.columns):
                        cell_content = ""
                        if pd.notna(row[col_name]):
                            if col_name == 'Timestamp':
                                try:
                                    cell_content = pd.to_datetime(row[col_name]).strftime('%H:%M:%S')
                                except:
                                    cell_content = str(row[col_name])
                            else:
                                cell_content = str(round(row[col_name], 2))
                        pdf.cell(ftp_header_widths[i], 7, cell_content, 1, 0, 'L')
                    pdf.ln()
            else:
                pdf.multi_cell(0, 7, "Keine FTP-Daten zur Anzeige verfügbar.")
            pdf.ln(10)
            #pdf.add_page()
        else:
            pdf.add_page()
            pdf.set_xy(pdf.l_margin, pdf.t_margin)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt="4. FTP-Testdaten:", ln=True, align="L")
            pdf.set_font("Arial", size=10)
            pdf.ln(2)
            #pdf.set_x(pdf.l_margin)
            pdf.multi_cell(available_width - 1, 7, "Keine FTP-Testdaten oder zugehörige Grafik für diesen Bericht verfügbar. Bitte laden Sie eine FTP-Datei im 'FTP-Test'-Tab hoch.")
            pdf.ln(10)
            #pdf.add_page()


        # --- 5. Trainingsplan ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt="5. Trainingsplan:", ln=True, align="L")
        pdf.set_font("Arial", size=10)
        pdf.ln(2)

        col_widths_training = [30, 70, 40, 40]
        display_columns_training = ["Tag", "Übung", "Dauer (Min.)", "Intensität"]

        pdf.set_fill_color(200, 220, 255)

        for i, header in enumerate(display_columns_training):
            pdf.cell(col_widths_training[i], 7, header, 1, 0, 'C', 1)
        pdf.ln()

        for index, row in training_plan_df.iterrows():
            for i, col_name in enumerate(display_columns_training):
                cell_content = str(row[col_name]) if pd.notna(row[col_name]) else ""
                pdf.cell(col_widths_training[i], 7, cell_content, 1, 0, 'L')
            pdf.ln()

        return bytes(pdf.output(dest='S'))


    
    st.markdown('<div class="versteckter-inhalt"></div>', unsafe_allow_html=True)


   # Dies ist der Button, der die PDF-Generierung auslöst.
    if st.button("Gesamten Bericht als PDF exportieren"):
        selected_person_name = st.session_state.get('person_select_box', '')

        if selected_person_name:
            person_data_for_report = st.session_state.get('selected_person_full_data')
            hf_zones_df_for_report = st.session_state.get('hf_zones_df')
            training_plan_df_for_report = st.session_state.get('training_plan_df')
            hf_graphic_buffer_for_report = st.session_state.get('hf_graphic_buffer')

            # --- NEUE DEBUG-AUSGABEN HIER EINFÜGEN ---
            # Diese Zuweisungen sind korrekt und sollten am Anfang stehen
            ekg_data_for_report = st.session_state.get('current_ekg_data')
            ekg_graphic_buffer_for_report = st.session_state.get('ekg_graphic_buffer')
            ftp_data_for_report = st.session_state.get('current_ftp_data') 
            ftp_graphic_buffer_for_report = st.session_state.get('ftp_graphic_buffer') 

            import sys
            import io # Stelle sicher, dass io importiert ist

            print(f"\n--- EKG-Debugging vor PDF-Erstellung ---", file=sys.stderr)
            print(f"ekg_data_for_report is None: {ekg_data_for_report is None}", file=sys.stderr)
            # DIESE ZEILE IST DIE WICHTIGE ÄNDERUNG, die den AttributeError verhindert
            if ekg_data_for_report is not None: 
                print(f"ekg_data_for_report.empty: {ekg_data_for_report.empty}", file=sys.stderr)
                if not ekg_data_for_report.empty:
                    print(f"ekg_data_for_report columns: {ekg_data_for_report.columns.tolist()}", file=sys.stderr)
                    print(f"ekg_data_for_report head:\n{ekg_data_for_report.head()}", file=sys.stderr)
            # Die folgende Zeile ist redundant, da ekg_graphic_buffer_for_report schon oben zugewiesen wurde
            # ekg_graphic_buffer_for_report = st.session_state.get('ekg_graphic_buffer') 
            print(f"ekg_graphic_buffer_for_report is None: {ekg_graphic_buffer_for_report is None}", file=sys.stderr)
            if ekg_graphic_buffer_for_report is not None:
                try:
                    current_pos = ekg_graphic_buffer_for_report.tell()
                    ekg_graphic_buffer_for_report.seek(0, io.SEEK_END)
                    buffer_size = ekg_graphic_buffer_for_report.tell()
                    ekg_graphic_buffer_for_report.seek(current_pos) # Reset to original position
                    print(f"ekg_graphic_buffer_for_report size: {buffer_size} bytes", file=sys.stderr)
                except Exception as e:
                    print(f"Could not determine EKG buffer size: {e}", file=sys.stderr)
            print(f"--- Ende EKG-Debugging ---", file=sys.stderr)


            print(f"\n--- FTP-Debugging vor PDF-Erstellung ---", file=sys.stderr)
            print(f"ftp_data_for_report is None: {ftp_data_for_report is None}", file=sys.stderr)
            # Auch hier die WICHTIGE ÄNDERUNG: if ftp_data_for_report is not None:
            if ftp_data_for_report is not None:
                print(f"ftp_data_for_report.empty: {ftp_data_for_report.empty}", file=sys.stderr)
                if not ftp_data_for_report.empty:
                    print(f"ftp_data_for_report columns: {ftp_data_for_report.columns.tolist()}", file=sys.stderr)
                    print(f"ftp_data_for_report head:\n{ftp_data_for_report.head()}", file=sys.stderr)
            print(f"ftp_graphic_buffer_for_report is None: {ftp_graphic_buffer_for_report is None}", file=sys.stderr)
            if ftp_graphic_buffer_for_report is not None:
                try:
                    current_pos = ftp_graphic_buffer_for_report.tell()
                    ftp_graphic_buffer_for_report.seek(0, io.SEEK_END)
                    buffer_size = ftp_graphic_buffer_for_report.tell()
                    ftp_graphic_buffer_for_report.seek(current_pos)
                    print(f"ftp_graphic_buffer_for_report size: {buffer_size} bytes", file=sys.stderr)
                except Exception as e:
                    print(f"Could not determine FTP buffer size: {e}", file=sys.stderr)
            print(f"--- Ende FTP-Debugging ---", file=sys.stderr)
            # WICHTIG: Die PDF-Generierung wird nur gestartet, wenn eine Person ausgewählt ist.
            # Fehlen andere Daten (EKG, FTP), werden diese im PDF als 'Nicht verfügbar' angezeigt.
            if person_data_for_report:
                pdf_output = create_training_report_pdf(
                    person_data_for_report,
                    hf_zones_df_for_report,
                    training_plan_df_for_report,
                    hf_graphic_buffer_for_report,
                    ekg_data_for_report,
                    ekg_graphic_buffer_for_report,
                    ftp_data_for_report,
                    ftp_graphic_buffer_for_report
                )
                
                st.download_button(
                    label="PDF jetzt herunterladen",
                    data=pdf_output,
                    file_name=f"Sporttest_Bericht_{selected_person_name.replace(' ', '_')}_{date.today().isoformat()}.pdf",
                    mime="application/pdf"
                )
                st.success("PDF-Bericht erfolgreich erstellt. Klicken Sie auf 'PDF jetzt herunterladen', um die Datei zu speichern.")
            else:
                # Dies sollte nur sehr selten auftreten, wenn eine Person ausgewählt war,
                # aber die Details plötzlich nicht mehr im Session State sind.
                st.warning("Die Daten der ausgewählten Person konnten nicht geladen werden. Bitte versuchen Sie es erneut oder wählen Sie eine andere Person.")
        else:
            st.warning("Bitte wählen Sie zuerst eine Person im Tab 'Daten' aus, um einen Bericht zu exportieren.")





