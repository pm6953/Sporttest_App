import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
def load_data(path='data/activities/activity.csv'):
    df = pd.read_csv(path)
    t_end = len(df)
    time = pd.Series(range(t_end))
    df["time"] = time
    return df

def create_powercurve_df(df, window_sizes=[1, 5, 10, 30, 60, 300, 600, 1800,3600]):
    all_effort = []
    for window in window_sizes:
        # Gleitender Durchschnitt für das jeweilige Zeitfenster und davon der höchste Wert
        best_power = find_best_effort(df["PowerOriginal"], window)
        all_effort.append(best_power)
    df_2 = pd.DataFrame({
    'time': window_sizes,
    'power': all_effort
})
    return df_2

def find_best_effort(series, window_size):
    best_effort=series.rolling(window=window_size).mean().max()
    return best_effort


def plot_powercurve(df,title):
    x=df.iloc[:,0]
    y=df.iloc[:,1]

    fig, ax= plt.subplots(figsize=(10, 6))
    ax.plot(x, y, marker='o')
    
    xlabel = x.name if x.name else "x"
    ylabel = y.name if y.name else "y"

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.show()
    fig.savefig(title.replace(' ', '_')+".png")
    return fig 


if __name__ == "__main__":
    

    #df_1=load_data()
    #print(df_1.head())
    #print("df_1[Poweroriginal] ist:",df_1["PowerOriginal"])
    #best_effort=find_best_effort(df_1["PowerOriginal"],120)
    #print("besteffort ist:",best_effort)
    #df_2 = create_powercurve_df(df_1)
    #print("df2ist:",df_2)
    #plot_powercurve(df_2,"Leistungsdiagramm")

    
    df_2=create_powercurve_df(load_data())
    plot_powercurve(df_2,"Leistungsdiagramm")
