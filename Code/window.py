import tkinter as tk
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mlt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime as dt
import sys

sns.set_theme(style="darkgrid")

def create_window(root: tk.Tk, prices: list, companies: list):
    end_time = dt.fromtimestamp(prices[0][1][0])

    df = pd.DataFrame([], columns=["Timestamp"])
    for counter, timing in enumerate(prices[0][1]):
        df.loc[counter] = pd.Timestamp(timing, unit='s')
    
    df['Date'] = df['Timestamp'].apply(lambda time: time.date())
    df['Date_Ordinal'] = pd.to_datetime(df['Date']).apply(lambda date: date.toordinal())

    figure = plt.figure(figsize=(10, 9))
    sns.set_palette(sns.color_palette("hls", len(prices)))
    for counter, price in enumerate(prices):
        sns.lineplot(x=df['Date'], y=price[0], label=f"{companies[counter].name}")

    plt.gca().xaxis.set_major_formatter(mlt.DateFormatter('%m/%d/%Y'))
    plt.xticks(rotation=45)
    plt.xlabel('Day')
    plt.ylabel('Average Price (USD)')
    plt.title(f'Volume Weighted Average Prices since {end_time.strftime('%m/%d/%Y')}')
    root.title(f'Volume Weighted Average Prices')

    canvas = FigureCanvasTkAgg(figure, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)