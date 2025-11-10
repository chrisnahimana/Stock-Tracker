from datetime import datetime, date, timedelta
import polygon
import stocks
import os
import sqlite3
import sys
import urllib3
import window
import tkinter as tk

api_key = str(os.environ.get("POLYGON_API_KEY"))
main_client = polygon.RESTClient(api_key)
con = sqlite3.connect('Code/storage/stocks.db')
stock = stocks.Stock(con)

def on_close():
   sys.exit() 

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

    try:
        for ticker in main_client.list_tickers(market="stocks", search=f"{symbol}", active="true", order="asc", limit=50, sort="ticker"):
            if len(tickers) < 50:
                tickers.append(ticker)
            else:
                break
    except urllib3.exceptions.MaxRetryError:
        sys.exit("No internet connection.")
    
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

    try:
        for prices in main_client.list_aggs(symbol, 1, "day", f"{end.strftime('%Y-%m-%d')}", f"{start.strftime('%Y-%m-%d')}"):
            opening_prices[0].append(prices.vwap)
            opening_prices[1].append(float(str(prices.timestamp)[:-3]))
    except urllib3.exceptions.MaxRetryError:
        sys.exit("No internet connection.")
        
    return opening_prices

def main():
    current_prices = []
    companies = []

    stock.all_stocks('f')

    secondary_window = window.Window(300, 100)
    secondary_window.retrieve_input(["Companies", "Timerange"])
    tk.mainloop()
    company_names = secondary_window.response.replace(", ", ",").split(",")
    time_range = secondary_window.time_range

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
        end_time =  start_time - timedelta(days=date_checked[1])
    elif time_range.lower() == "max":
        end_time =  start_time - timedelta(days=730)
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
    
    main_window = window.Window()
    main_window.create_window(current_prices, companies)
    tk.mainloop()

main()
con.close()