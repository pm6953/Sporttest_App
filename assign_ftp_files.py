from read_persondata import Person
from fit_reader import FTP_Test  # das ist jetzt deine Klasse mit read_fit_file-Methode
import os

# 1. FIT-Dateipfade
fit1_path = "data/Stufentest_data/FTP_File_1.fit"
fit2_path = "data/Stufentest_Data/FTP_File_2.fit"

# 2. Robuste Namenssuche
def find_by_name(target_name):
    target_name = target_name.strip().lower()
    for p in Person.load_person_data():
        name = f"{p['firstname']} {p['lastname']}".strip().lower()
        if name == target_name:
            return p
    return None

julian = find_by_name("Julian Huber")
yannic = find_by_name("Yannic Heyer")

print("Julian gefunden:", julian is not None)
print("Yannic gefunden:", yannic is not None)

if not julian or not yannic:
    raise Exception("Eine oder beide Personen wurden nicht gefunden.")

# 3. FTP-Testobjekte mit deiner Klasse erstellen
ftp_test_1 = FTP_Test(fit1_path)
ftp_test_2 = FTP_Test(fit2_path)

# 4. Zusammenfassung auslesen (optional zur Kontrolle)
print("Julian FTP-Test Summary:", ftp_test_1.get_summary())
print("Yannic FTP-Test Summary:", ftp_test_2.get_summary())

# 5. In Personendaten eintragen
persons = Person.load_person_data()

def create_ftp_test_entry(new_id, filepath):
    return {
        "id": new_id,
        "date": "2025-07-02",  # Oder dynamisch: str(date.today())
        "result_link": os.path.abspath(filepath)
    }

# Neue eindeutige ID generieren
existing_ids = [test["id"] for p in persons for test in p.get("ftp_tests", [])]
new_id_1 = max(existing_ids + [0]) + 1
new_id_2 = new_id_1 + 1

for p in persons:
    if p["id"] == julian["id"]:
        p.setdefault("ftp_tests", []).append(create_ftp_test_entry(new_id_1, fit1_path))
    if p["id"] == yannic["id"]:
        p.setdefault("ftp_tests", []).append(create_ftp_test_entry(new_id_2, fit2_path))

Person.save_person_data(persons)

print("FTP-Dateien erfolgreich zugewiesen und gespeichert.")
