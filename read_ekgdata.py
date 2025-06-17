import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#from person import load_by_id, calc_max_heart_rate, calc_age

# Klasse EKG-Data für Peakfinder, die uns ermöglicht peaks zu finden

class EKGdata:

## Konstruktor der Klasse soll die Daten einlesen

    def __init__(self, ekg_dict):
        #pass
        self.id = ekg_dict["id"]
        self.date = ekg_dict["date"]
        self.data = ekg_dict["result_link"]
        self.df = pd.read_csv(self.data, sep='\t', header=None, names=['Messwerte in mV','Zeit in ms',])
        self.df = self.df.iloc[:5000]  # Entferne die erste Zeile, da sie nur die Spaltennamen enthält
        self.person_firstname = ekg_dict.get("person_firstname", "")
        self.person_lastname = ekg_dict.get("person_lastname", "")
        self.date_of_birth = ekg_dict.get("date_of_birth", None)
    
    
    def auto_threshold(self, factor=1.5):
        
        #Bestimmt einen adaptiven Schwellenwert für die Peak-Erkennung
        mean_val = self.df['Messwerte in mV'].mean()
        std_val = self.df['Messwerte in mV'].std()
        threshold = mean_val + factor * std_val

        return threshold

    
    def plot_time_series(self, threshold = None, respacing_factor = 5):

        if threshold is None:
            threshold = self.auto_threshold()

        # Daten vorbereiten
        df_plot = self.df.head(2000)
        peaks = self.find_peaks(threshold, respacing_factor)
        peaks = [p for p in peaks if p < 2000]
        peak_df = self.df.iloc[peaks]

    # Plot erstellen
        plt.figure(figsize=(12, 5))
        plt.plot(df_plot["Zeit in ms"], df_plot["Messwerte in mV"], label="EKG-Signal")
        plt.scatter(peak_df["Zeit in ms"], peak_df["Messwerte in mV"], color='red', label="Peaks")

        plt.xlabel("Zeit in ms")
        plt.ylabel("Messwerte in mV")
        plt.title("EKG Zeitreihe mit Peaks")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

    # Zeige den Plot direkt im Fenster
        plt.show()

    def find_peaks(self, threshold, respacing_factor=5):
        series=self.df['Messwerte in mV']
    # Respace the series
        series = series.iloc[::respacing_factor]
    
    # Filter the series
        series = series[series>threshold]


        peaks = []
        last = 0
        current = 0
        next = 0

        for index, row in series.items():
            last = current
            current = next
            next = row

            if last < current and current > next and current > threshold:
                peaks.append(index-respacing_factor)

        return peaks

    def estimate_hr(self, threshold, respacing_factor=5):
        
        peaks = self.find_peaks(threshold, respacing_factor)

        # Prüfen, ob genügend Peaks vorhanden sind
        if len(peaks) < 2:
            return None  # Zu wenig Daten für Berechnung

        # Berechne Zeitabstände zwischen den Peaks mit numpy
        time_stamps = self.df.iloc[peaks]['Zeit in ms'].values
        rr_intervals = np.diff(time_stamps)  # in ms

        # Durchschnittliches RR-Intervall in Millisekunden
        avg_rr = np.mean(rr_intervals)

        # Herzfrequenz in bpm berechnen
        hr_bpm = 60000 / avg_rr  # 60.000 ms pro Minute

        return round(hr_bpm, 2)


    @staticmethod
    def load_by_id(ekg_test_id, persons_list):
    
        #Lädt einen EKG-Test anhand der EKG-Test-ID und der Personenliste.
        
        for person in persons_list:
            for ekg_test in person.get("ekg_tests", []):
                if ekg_test["id"] == ekg_test_id:
                    ekg_dict = {
                        "id": ekg_test["id"],
                        "date": ekg_test["date"],
                        "result_link": ekg_test["result_link"],
                        "person_firstname": person.get("firstname"),
                        "person_lastname": person.get("lastname"),
                        "person_id": person.get("id"),
                        "date_of_birth": person.get("date_of_birth"),
                    }
                    return EKGdata(ekg_dict)

        raise ValueError(f"EKG-Test mit ID {ekg_test_id} nicht gefunden.")


if __name__ == "__main__":
    print("This is a module with some functions to read the EKG data")
    file = open("data/person_db.json")
    person_data = json.load(file)
    ekg_dict = person_data[0]["ekg_tests"][0]
    print(ekg_dict)
    ekg = EKGdata(ekg_dict)
    print(ekg.df.head())

    threshold = ekg.auto_threshold()

    peaks=ekg.find_peaks(threshold)
    print(peaks)

    estimate_HeartRate = ekg.estimate_hr(threshold)
    print(estimate_HeartRate)

    ekg_test = ekg.load_by_id(2, person_data)

    print(ekg_test.id)
    print(ekg_test.date)
    print(ekg_test.person_firstname)

    ekg.plot_time_series(threshold)
    