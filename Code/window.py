import tkinter as tk
from tkinter.ttk import *
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mlt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime as dt
import sys

sns.set_theme(style="darkgrid")
top = None

class Window:
    def __init__(self, width: int = 1080, height: int = 720):
        self.root = tk.Tk()

        self.w = width
        self.h = height
        self.ws = self.root.winfo_screenwidth()
        self.hs = self.root.winfo_screenheight()
        self.center()

        self.company_var = tk.StringVar()
        self.time_var = tk.StringVar()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.response = ""
        self.time_range = ""
    
    def center(self):
        x = (self.ws/2) - (self.w/2)
        y = (self.hs/2) - (self.h/2)
        self.root.geometry('%dx%d+%d+%d' % (self.w, self.h, x, y))
    
    def on_close(self):
        sys.exit()

    def button_click(self):
        self.response = self.company_var.get()
        self.time_range = self.time_var.get()

        self.root.destroy()
        self.root.quit()

    def retrieve_input(self, queries: list):
        self.root.title("")
        company_names = Label(self.root, text=queries[0], font=('arial', 10, 'bold'))
        company = Entry(self.root, textvariable=self.company_var)
        timerange = Label(self.root, text=queries[1], font=('arial', 10, 'bold'))
        time = Entry(self.root, textvariable=self.time_var)

        submit = Button(self.root, text="Enter", command=self.button_click)

        company_names.place(relx=0.25, rely=0.25, anchor='center')
        company.place(relx=0.6, rely=0.25, anchor='center')
        timerange.place(relx=0.25, rely=0.5, anchor='center')
        time.place(relx=0.6, rely=0.5, anchor='center')
        submit.place(relx=0.5, rely=0.8, anchor='center')

    def create_window(self, prices: list, companies: list):
        end_time = dt.fromtimestamp(prices[0][1][0])

        df = pd.DataFrame([], columns=["Timestamp"])
        for counter, timing in enumerate(prices[0][1]):
            df.loc[counter] = pd.Timestamp(timing, unit='s')
        
        df['Date'] = df['Timestamp'].apply(lambda time: time.date())
        df['Date_Ordinal'] = pd.to_datetime(df['Date']).apply(lambda date: date.toordinal())

        figure = plt.figure(figsize=(10, 9))
        sns.set_palette(sns.color_palette("hls", len(prices)))
        for counter, price in enumerate(prices):
            try:
                sns.lineplot(x=df['Date'], y=price[0], label=f"{companies[counter].name}")
            except ValueError:
                sys.exit(f"{companies[counter].name} has {len(price[0])} days but only {len(df['Date'])} days are available.")

        plt.gca().xaxis.set_major_formatter(mlt.DateFormatter('%m/%d/%Y'))
        plt.xticks(rotation=45)
        plt.xlabel('Day')
        plt.ylabel('Average Price (USD)')
        plt.title(f'Volume Weighted Average Prices since {end_time.strftime('%m/%d/%Y')}')
        self.root.title(f'Volume Weighted Average Prices')

        canvas = FigureCanvasTkAgg(figure, master=self.root)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)