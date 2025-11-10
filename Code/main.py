import matplotlib.pyplot as plt
import matplotlib.dates as mlt
import pandas as pd
import seaborn as sns
from datetime import datetime
from datetime import date
from datetime import timedelta
import polygon
import stocks
import os
import sqlite3
import sys

sns.set_theme(style="whitegrid")
api_key = str(os.environ.get("POLYGON_API_KEY"))
main_client = polygon.RESTClient(api_key)
con = sqlite3.connect('Code/storage/stocks.db')
stock = stocks.Stock(con)

def dating_check(query: str):
    key_characters  = ["w", "m", "y"]
    try:
        for char in key_characters:
            if char in query:
                if char == "w":
                    return (True, int(query[:-1])*7)
                elif char == "m":
                    return (True, int(query[:-1])*30)
                elif char == "y":
                    return (True, int(query[:-1])*365)
    except ValueError:
        return (False, 0)
            
    return (False, 0)

def search(symbol: str):
    tickers = []

    for ticker in main_client.list_tickers(market="stocks", search=f"{symbol}", active="true", order="asc", limit=50, sort="ticker"):
        if len(tickers) < 50:
            tickers.append(ticker)
        else:
            break
    
    for tick in tickers:
        if tick.ticker == symbol:
             return tick
        else:
            continue
    
    try:
        return tickers[0]
    except IndexError:
        sys.exit(f"{symbol} doesn't exist!")

def find(symbol: str, start: datetime, end: datetime):
    opening_prices = [[], []]

    for prices in main_client.list_aggs(symbol, 1, "day", f"{end.strftime('%Y-%m-%d')}", f"{start.strftime('%Y-%m-%d')}"):
        opening_prices[0].append(prices.vwap)
        opening_prices[1].append(float(str(prices.timestamp)[:-3]))
        
    return opening_prices

def main():
    current_prices = []
    companies = []

    stock.all_stocks('s')
    company_names = str(input("Companies (Seperated by ,): ")).replace(", ", ",").split(",")
    time_range = input("Timeframe: ")

    end_time = None
    start_time = datetime.today()
    date_checked = dating_check(time_range)

    if "-" in time_range:
        time_range = time_range.split("-")
        start_time = time_range[0].split("/")
        end_time = time_range[1].split("/")

        start_time = datetime.combine(date(int(start_time[2]), int(start_time[0]), int(start_time[1])), datetime.min.time())
        end_time =  datetime.combine(date(int(end_time[2]), int(end_time[0]), int(end_time[1])), datetime.min.time())
    elif date_checked[0]:
        end_time =  datetime.today() - timedelta(days=date_checked[1])
    elif time_range.lower() == "max":
        end_time =  datetime.today() - timedelta(days=730)
    else:
        try:
            if int(time_range) <= 1:
                sys.exit("Please input a date greater than 1!")

            end_time =  datetime.today() - timedelta(days=int(time_range))
        except ValueError:
            time_range = time_range.split("/")
            try:
                end_time =  datetime.combine(date(int(time_range[2]), int(time_range[0]), int(time_range[1])), datetime.min.time())
            except IndexError:
                sys.exit("Please enter a proper date!")

    if company_names[0].lower() == "all":
        company_names = stock.all_stocks("a")

    for name in company_names:
        company = stock.ticker(name)
        if company == None:
            company = search(name)

        companies.append(company)
        pricing = stock.retrieve(company, start_time, end_time)

        if pricing == None:
            pricing = find(company.ticker, start_time, end_time)
            stock.addin(company, pricing[0], pricing[1])

        current_prices.append(pricing)

    df = pd.DataFrame([], columns=["Timestamp"])
    for counter, timing in enumerate(current_prices[0][1]):
        df.loc[counter] = pd.Timestamp(timing, unit='s')
    
    df['Date'] = df['Timestamp'].apply(lambda time: time.date())
    df['Date_Ordinal'] = pd.to_datetime(df['Date']).apply(lambda date: date.toordinal())

    plt.figure(figsize=(10, 8))
    sns.set_palette(sns.color_palette("hls", len(current_prices)))
    for counter, price in enumerate(current_prices):
        sns.lineplot(x=df['Date'], y=price[0], label=f"{companies[counter].name}")

    plt.gca().xaxis.set_major_formatter(mlt.DateFormatter('%m/%d/%Y'))
    plt.xticks(rotation=45)
    plt.xlabel('Day')
    plt.ylabel('Average Price (USD)')
    plt.title(f'Volume Weighted Average Prices since {end_time.strftime('%m/%d/%Y')}')
    plt.legend(loc='upper left')
    plt.show()

main()
con.close()