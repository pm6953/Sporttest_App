import json
from datetime import datetime
class Person:
    
    @staticmethod
    def load_person_data():
        """A Function that knows where te person Database is and returns a Dictionary with the Persons"""
        file = open("data/person_db.json")
        person_data = json.load(file)
        return person_data

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
        birthyear = self.date_of_birth
        age= datetime.today().year-birthyear
        print()
        return age

    def calc_max_heart_rate(self):
        gender=self.gender
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
    