import pandas as pd
import json

class FTP_Test:
    #zeigt wie es hinterlegt ist bei der person_db.json Datei
    #"fit_test": [
           # {
               # "id": 1,
               # "date": "16.8.2023",
                #"result_link": "data/Stufentest_data/6817599882_ACTIVITY.fit"
          #  }
      #  ]

    def __init__(self, ftp_dict):
        self.id = ftp_dict["id"]
        self.date = ftp_dict["date"]
        self.data = ftp_dict["result_link"]
        self.df = pd.read_csv(self.data, sep='\t', header=None, names=['Messwerte in mV','Zeit in ms',])

    #liest die maximale Herzfrequenz aus den fitfiles
    def max_estimate_hr(self):
        pass

    @staticmethod
    def load_by_id(ftp_test_id, persons_list):
    
        #Lädt einen EKG-Test anhand der EKG-Test-ID und der Personenliste.
        
        for person in persons_list:
            for ftp_test in person.get("ftp_tests", []):
                if ftp_test["id"] == ftp_test_id:
                    ftp_dict = {
                        "id": ftp_test["id"],
                        "date": ftp_test["date"],
                        "result_link": ftp_test["result_link"],
                        "person_firstname": person.get("firstname"),
                        "person_lastname": person.get("lastname"),
                        "person_id": person.get("id"),
                        "date_of_birth": person.get("date_of_birth"),
                    }
                    return FTP_Test(ftp_dict)

        raise ValueError(f"FTP-Test mit ID {ftp_test_id} nicht gefunden.")

if __name__ == "__main__":
    print("This is a module with some functions to read the EKG data")
    file = open("data/person_db.json")
    person_data = json.load(file)
    fit_dict = person_data[0]["ftp_tests"][0]
    
            
        
