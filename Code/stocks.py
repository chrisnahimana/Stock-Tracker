from datetime import datetime
import sqlite3 as sq
import polygon.rest.models.tickers as poly

class Ticker:
    def __init__(self, ticker, name):
        self.name = name
        self.ticker = ticker
        self.high = 0
        self.low = 0
    
    def set_high(self, price: int):
        self.high = price
    
    def set_low(self, price: int):
        self.low = price


class Stock:
    def __init__(self, connection: sq.Connection):
        self.con = connection
        cur = self.con.cursor()
        cur.execute(f"""CREATE TABLE IF NOT EXISTS names(ticker, name)""")
        self.con.commit()
        cur.close()

    def addin(self, ticker: Ticker | poly.Ticker, prices: list, dates: list):
        cur = self.con.cursor()

        # Makes sure a table exists for the given ticker before attempting to do anything else
        cur.execute(f"""CREATE TABLE IF NOT EXISTS {ticker.ticker}(price FLOAT, timestamp FLOAT UNIQUE)""")
        self.con.commit()

        # Creates entry in names if the company isn't already inside it (I case the function is only updating the days)
        try:
            cur.execute(f"""SELECT * FROM names WHERE ticker=?""", (ticker.ticker,))
            res = cur.fetchall()
            if res == []:
                raise sq.OperationalError
        except sq.OperationalError:
            cur.execute(f"""INSERT INTO names VALUES (?, ?)""", (ticker.ticker, ticker.name))

        # Makes sure the price and dates get locked together and won't go out of order
        data = zip(prices, dates)
        for unit in data:
            try:
                cur.execute(f"""INSERT INTO {ticker.ticker} VALUES (?, ?)""", (unit[0], unit[1]))
            except sq.IntegrityError:
                continue
        
        self.con.commit()
        cur.close()
    
    def retrieve(self, ticker, start_date:datetime, end_date: datetime):
        cur = self.con.cursor()

        try:
            # Grabs the oldest and newest dates in the tickers table
            cur.execute(f"""SELECT MIN(timestamp) FROM {ticker.ticker}""")
            oldest_time = float(cur.fetchall()[0][0])
            cur.execute(f"""SELECT MAX(timestamp) FROM {ticker.ticker}""")
            newest_time = float(cur.fetchall()[0][0])

            # Checks to make sure the end date isn't older than the oldest date available
            # Also checks to make sure it is a weekday (No need to update if its end_date is Saturday (11/08) but the oldest avaliable is Monday (11/10) as markets are closed
            if end_date.timestamp() < oldest_time and end_date.weekday() < 5:
                cur.close()
                return None
            
            # Ensures the difference between the newest date and the start date isn't more than one day when it isn't Sunday or Monday as markets are closed on weekends
            # Also ensures that the start date isn't today as Polygon updates at nonstandard times which could lead to a 2 day difference
            elif abs(start_date.timestamp() - newest_time) >= 172800 and start_date.weekday() not in [0, 6] and abs(start_date.timestamp() - datetime.today()) >= 172800:
                cur.close()
                return None

            # Collects the correct date
            cur.execute(f"""SELECT price, timestamp FROM {ticker.ticker} WHERE timestamp>=? AND timestamp<=? ORDER BY timestamp ASC""", (end_date.timestamp(), start_date.timestamp()))
            data = cur.fetchall()
        except sq.OperationalError:
            # Returns None if the table for the ticker doesn't exist, allowing it to be added later
            cur.close()
            return None

        # Formatts the return data to be a list formmated as [List of Prices, List of Timestamps] with them being directly linked
        return_data = [[], []]
        for pricepoint in data:
            return_data[0].append(pricepoint[0])
            return_data[1].append(pricepoint[1])

        cur.close()
        return return_data
    
    def ticker(self, query: str):
        cur =  self.con.cursor()
        ticker = None
        
        # Query's the names table for a given ticker
        try: 
            cur.execute(f"""SELECT name FROM names WHERE ticker='{query}'""")
            res = cur.fetchall()
            ticker = Ticker(query, res[0][0])
        except (IndexError, sq.OperationalError):
            # Grabs all the names in the names table and does a partial search for the name in cause the query isn't a ticker Display Symbol
            cur.execute(f"""SELECT * FROM names""")
            res = cur.fetchall()
            for name in res:
                if query in name[1]:
                    ticker = Ticker(name[0], name[1])

        cur.close()
        return ticker
    
    def all_stocks(self, format="full"):
        cur = self.con.cursor()

        if format == "full" or format == "f":
            cur.execute(f"""SELECT * FROM names""")
            res = cur.fetchall()
            for ticker in res:
                cur.execute(f"""SELECT * FROM '{ticker[0]}'""")
                tick = cur.fetchall()

                cur.execute(f"""SELECT MAX(timestamp) FROM {ticker[0]}""")
                new = cur.fetchall()[0][0]
                cur.execute(f"""SELECT MIN(timestamp) FROM {ticker[0]}""")
                old = cur.fetchall()[0][0] 

                print(f"{ticker[0]} ({ticker[1]}): {datetime.fromtimestamp(old).strftime("%b %d, %Y")} to {datetime.fromtimestamp(new).strftime("%b %d, %Y")} ({len(tick)} Days)")
        elif format == "simple" or format == "s":
            cur.execute(f"""SELECT * FROM names""")
            res = cur.fetchall()
            print(f"{len(res)} Comapnies Cached")
        elif format == "all" or format == "a":
            cur.execute(f"""SELECT ticker FROM names""")
            res = cur.fetchall()
            tickers = []
            for tick in res:
                tickers.append(tick[0])
            cur.close()
            return tickers
        
        cur.close()
