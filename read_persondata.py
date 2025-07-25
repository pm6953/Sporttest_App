from email.headerregistry import Address
import json
from datetime import datetime
import os

class Person:
    
    @staticmethod
    def load_person_data():
        """A Function that knows where the person Database is and returns a Dictionary with the Persons"""
        # Stellen Sie sicher, dass die Datei existiert, bevor Sie versuchen, sie zu öffnen
        if not os.path.exists("data/person_db.json"):
            # Optional: Eine leere Liste zurückgeben oder eine leere Datei erstellen
            return []
        with open("data/person_db.json", 'r', encoding="utf-8") as file:
            person_data = json.load(file)
        return person_data

    @staticmethod
    def save_person_data(person_list):
        """Saves the given list of persons back to the JSON database."""
        # Sicherstellen, dass das 'data' Verzeichnis existiert
        os.makedirs("data", exist_ok=True)
        with open("data/person_db.json", "w", encoding="utf-8") as f:
            json.dump(person_list, f, ensure_ascii=False, indent=4)

    @staticmethod
    def delete_person_by_id(person_id):
        """Deletes a person from the database by their ID."""
        persons_list = Person.load_person_data()
        original_length = len(persons_list)
        # Filtern Sie die Liste, um alle Personen außer der zu löschenden Person zu behalten
        updated_persons_list = [p for p in persons_list if int(p["id"]) != int(person_id)]

        if len(updated_persons_list) < original_length:
            Person.save_person_data(updated_persons_list)
            return True # Erfolgreich gelöscht
        return False
     # Person nicht gefunden oder nicht gelöscht

    @staticmethod
    def replace_person_data(person_id, new_data):
        persons = Person.load_person_data()
        for i, p in enumerate(persons):
            if p["id"] == person_id:
                persons[i] = new_data
                Person.save_person_data(persons)
                return True
        return False 
    @staticmethod
    def get_person_list(person_data):
        """A Function that takes the persons-dictionary and returns a list auf all person names"""
        list_of_names = []

        for eintrag in person_data:
            list_of_names.append(eintrag["lastname"] + ", " +  eintrag["firstname"])
        return list_of_names
    
    @staticmethod
    def find_person_data_by_name(suchstring):
        """ Eine Funktion der Nachname, Vorname als ein String übergeben wird
        und die die Person als Dictionary zurück gibt"""

        person_data = Person.load_person_data()
        #print(suchstring)
        if suchstring == "None":
            return {}

        two_names = suchstring.split(", ")
        if len(two_names) < 2:
            return None
        
        vorname = two_names[1]
        nachname = two_names[0]

        for eintrag in person_data:
            print(eintrag)
            if (eintrag["lastname"] == nachname and eintrag["firstname"] == vorname):
                print()

                return eintrag
        else:
            return {}
    @staticmethod   
    def load_by_id(suchid):
        person_data = Person.load_person_data()
        if suchid == "None":
            return{}
        
        for eintrag in person_data:
            
            if (eintrag ["id"] == suchid):
                return eintrag
            else:
                return {}
            
    def calc_age(self):
        birthyear = datetime.strptime(self.date_of_birth, "%Y-%m-%d")
        age= (datetime.today() - birthyear).days//365
        print()
        return age

    def calc_max_heart_rate(self):
        gender = self.gender
        if gender == "male":
            max_hr_bpm =  223 - 0.9 * self.calc_age()
            return max_hr_bpm
        elif gender == "female":
            max_hr_bpm = 226 - 1.0 *  self.calc_age()
            return max_hr_bpm
        

    def __init__(self, person_dict) -> None:
        self.date_of_birth = person_dict["date_of_birth"]
        self.firstname = person_dict["firstname"]
        self.lastname = person_dict["lastname"]
        self.picture_path = person_dict["picture_path"]
        self.id = person_dict["id"]
        self.gender = person_dict["gender"]
        self.address = person_dict.get("address", "")


if __name__ == "__main__":
    #print("This is a module with some functions to read the person data")
    #persons = Person.load_person_data()
    #person_names = Person.get_person_list(persons)
    #print(person_names)
    #print(Person.find_person_data_by_name("Huber, Julian"))
    dict_person1= Person.load_by_id(1)
    print(dict_person1)
    #print(dict_person1["age"])
    #heartrate1= Person.calc_max_heart_rate(dict_person1["age"],dict_person1["gender"])
    #print("Herzrate=",heartrate1)
    testperson= Person(dict_person1)
    person_age= testperson.calc_age()
    print(person_age)
    Herzrate=testperson.calc_max_heart_rate()
    print(Herzrate)
    