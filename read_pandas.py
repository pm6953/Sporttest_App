# Paket für Bearbeitung von Tabellen
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# Paket
## zuvor !pip install plotly
## ggf. auch !pip install nbformat
import plotly.express as px
import plotly.io as pio
pio.renderers.default = "browser"

def read_my_csv():
    # Einlesen eines Dataframes
    ## "\t" steht für das Trennzeichen in der txt-Datei (Tabulator anstelle von Beistrich)
    ## header = None: es gibt keine Überschriften in der txt-Datei
    df = pd.read_csv("data/activities/activity.csv")

    t_end= len(df)
    time = np.arange(0, t_end)
    df ["time"] = time
    return df

def erstelle_hr_zonen_plot(df, max_hr):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()  # zweite Y-Achse (rechts)
    zonen = {
        "Zone 1": (max_hr * 0.50, max_hr * 0.60),
        "Zone 2": (max_hr * 0.60, max_hr * 0.70),
        "Zone 3": (max_hr * 0.70, max_hr * 0.80),
        "Zone 4": (max_hr * 0.80, max_hr * 0.90),
        "Zone 5": (max_hr * 0.90, max_hr * 1.00),
    }

    farben = {
        "Zone 1": "blue",
        "Zone 2": "green",
        "Zone 3": "yellow",
        "Zone 4": "orange",
        "Zone 5": "red",
    }

    zone_zeiten = {zone: 0 for zone in zonen}
    zone_power = {zone: [] for zone in zonen}

    zeit = df["time"] / 60  # Zeit in Minuten
    hf = df["HeartRate"]
    power = df["PowerOriginal"]

    # Hauptdiagramm mit zwei Y-Achsen
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()  # zweite Y-Achse (rechts)

    # Herzfrequenz-Zonen mit Farben zeichnen
    for i in range(len(zeit) - 1):
        wert = hf[i]
        for zone, (low, high) in zonen.items():
            if low <= wert < high:
                ax1.plot(zeit[i:i+2], hf[i:i+2], color=farben[zone], linewidth=2)
                zone_zeiten[zone] += 1
                zone_power[zone].append(power[i])
                break

    sekunden_pro_schritt = 1

    for zone, (low, high) in zonen.items():
        dauer_sek = zone_zeiten[zone] * sekunden_pro_schritt
        dauer_min = dauer_sek / 60

        if zone_power[zone]:
            avg_power = sum(zone_power[zone]) / len(zone_power[zone])
        else:
            avg_power = 0

        label = f"{zone} ({dauer_min:.1f} min, Ø {avg_power:.0f} W)"
        ax1.axhspan(low, high, color=farben[zone], alpha=0.05, label=label)


    # Leistung als Linie auf rechter Y-Achse zeichnen
    ax2.plot(zeit, power, color="grey", linewidth=1, label="Power (W)")

    # Achsentitel & Beschriftungen
    ax1.set_title("Herzfrequenz- und Leistungsdaten mit Trainingszonen")
    ax1.set_xlabel("Zeit (min)")
    ax1.set_ylabel("Herzfrequenz (bpm)")
    ax2.set_ylabel("Leistung (Watt)")

    ax1.set_xlim(left=0)
    ax1.grid(True)
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2,
           loc="upper left", bbox_to_anchor=(1.06, 1), borderaxespad=0.)
    plt.tight_layout(rect=[0, 0, 0.85, 1])  # Platz für Legende schaffen
    #plt.show()
    st.pyplot(fig)

def berechne_durchschnittswerte(df):
    durchschnitt_hf = df["HeartRate"].mean()
    durchschnitt_leistung = df["PowerOriginal"].mean()
    return durchschnitt_hf, durchschnitt_leistung

if __name__=="__main__":
    
    # Lese die Daten ein
    df = read_my_csv()
    if df is not None:
        try:
            max_hr = float(input("Gib deine maximale Herzfrequenz ein: "))
            erstelle_hr_zonen_plot(df, max_hr)
        except ValueError:
            print("Bitte eine gültige Zahl für die maximale Herzfrequenz eingeben.")
            exit()

