from fitparse import FitFile
import pandas as pd

class FTP_Test:
    def __init__(self, file_path, id=None, date=None, person_firstname=None, person_lastname=None):
        self.file_path = file_path
        self.id = id
        self.date = date
        self.person_firstname = person_firstname
        self.person_lastname = person_lastname
        self.data = self.read_fit_file()
        self.df = self.data



    def read_fit_file(self):
        try:
            fitfile = FitFile(self.file_path)
            records = []

            for record in fitfile.get_messages("record"):
                record_data = {}
                for field in record:
                    # Nur relevante Datenfelder übernehmen
                    if field.name in ["timestamp", "heart_rate", "power", "cadence", "speed"]:
                        record_data[field.name] = field.value
                if record_data:  # Nur wenn Daten vorhanden
                    records.append(record_data)

            df = pd.DataFrame(records)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)
            return df

        except Exception as e:
            print(f"Fehler beim Einlesen der FIT-Datei: {e}")
            return pd.DataFrame()  # Leeres DataFrame als Fallback

    def get_summary(self):
        if self.data.empty:
            return "Keine Daten vorhanden."
        return {
            "Dauer": self.data.index[-1] - self.data.index[0],
            "Durchschnittliche Herzfrequenz": round(self.data["heart_rate"].mean(), 1),
            "Maximale Leistung": self.data["power"].max()
        }

    def get_dataframe(self):
        return self.data
