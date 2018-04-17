import pandas_datareader as web
from glob import glob
import pandas as pd
import numpy as np
from math import sqrt

class SecurityData(object):
    
    def __init__(self, initial_amount = 10000000, mkt_cap = 500000000,\
                 trading_vol = 1000000, download_path = "data/", \
                 data_source = "yahoo", start_date = '2011-01-04', \
                 end_date = '2015-07-31', trade_volume_days = 15, \
                 verbose = False):
        
        self.initial_amount = initial_amount
        self.mkt_cap = mkt_cap
        self.trading_vol = trading_vol
        self.download_path = download_path
        self.data_source = data_source
        self.start_date = start_date
        self.end_date = end_date
        self.trade_volume_days = trade_volume_days
        self.verbose = verbose
        self.L = 90
        self.stdev_window = 62
        
    """path of fundamental datafiles"""
    def __get_funda_path(self, ticker):
        exchange = ticker[-2:].lower()
        path = "szss//"+exchange+"//"+ticker[:-2]+ exchange+"_factor.csv"
        return path
        
    "method to merge the market data in 1 file to be used in the Strategy class"
    def merge_market_data(self):
        
        universal_data = pd.DataFrame()
        
        "merging the files"
        files = glob(self.download_path+'*.csv')
        
        for file in files:
            ticker = file.split("\\")[1][:-4]
            
            trade_data = pd.read_csv(file)
            trade_data["ticker"] = ticker 
            trade_data["AverageVol"] = trade_data.Volume.rolling(window=self.trade_volume_days).mean().reset_index(0,drop=True)
            trade_data = trade_data.fillna(method='ffill')
            
            "appending to the final dataset only only if the stock passes the volume filter"
            try:
                if (trade_data.tail(1).Volume.iloc[0] >= self.trading_vol):
                    "reading the data from the csv file"
                    funda_data = pd.read_csv(self.__get_funda_path(ticker))
                    funda_data["ticker"] = ticker
                    
                    "merging the fundamental and timeseries data"
                    merged_data = pd.merge(funda_data, trade_data, how = "inner", on = ["Date","ticker"])
                    
                    "momentum factor"
                    merged_data["PM"] = np.log(merged_data["Adj Close"].shift(1)/merged_data["Adj Close"].shift(6))
                    merged_data["PRev"] = np.log(merged_data["Adj Close"].shift(21)/merged_data["Adj Close"].shift(1))
                    merged_data["DailyRet"] = merged_data["Adj Close"]/merged_data["Adj Close"].shift(1)
                    merged_data["Ret"] = np.log(merged_data["Adj Close"].shift(1)/merged_data["Adj Close"].shift(self.L + 1))
                    merged_data["Volatility"] = sqrt(250/self.L)*merged_data.Ret.rolling(window=self.stdev_window).std(ddof=0).reset_index(0,drop=True)
                    
                    universal_data = universal_data.append(merged_data)
            except:
                print ("error")
                pass
            
            if (self.verbose):
                print(f"ticker: {ticker} ")
        
        "exporting to csv"            
        universal_data = universal_data[["Date","ticker","Adj Close","DailyRet", "PB","PCF","PE","PS","PM","PRev","Volatility"]].dropna()
        return universal_data
    """end of function"""
    
    def fetch_timeseries_data(self, ticker_universe):
        """download the time series data from external source"""
        "cleaning the tickers"
        ticker_universe.ticker = ticker_universe.ticker.apply(lambda s: s[:-1]+'S' if s[:-1] == "H" else s).str.strip()
        
        "string to float conversion"
        ticker_universe.mktshare = ticker_universe.mktshare.str.replace(",","").astype(float)
        ticker_universe["avg_trade_volume"] = 0

        "market capitalization filter"
        ticker_universe = ticker_universe[ticker_universe.mktshare >= self.mkt_cap].reset_index()
        
        "loop for downloading the data"
        for i in range(0,len(ticker_universe)):
            ticker = ticker_universe.iloc[i,1].strip()
            
            "loop to try 5 times for downloading the data"
            retry_flag = 0
            
            while (retry_flag < 5):
                try:
                    data = web.DataReader(ticker, self.data_source, self.start_date, self.end_date)
                    data = data.fillna(method="ffill")
                    data = data.fillna(method="backfill")                    
                    data.to_csv(self.download_path+ticker+".csv")
                    if (self.verbose):
                        print(f"try {i}: flag : {retry_flag} : ticker : {ticker}")
                    break
                except Exception as e:
                    if (self.verbose):
                        print(f"except {i}: flag : {retry_flag} : ticker : {ticker}")
                    retry_flag = retry_flag +1
                    if (retry_flag  > 4):
                        if (self.verbose):
                            print (str(e))
                        continue
    """end of function"""
        
if __name__ == "__main__":
    security_data = SecurityData(verbose=True)
    universal_data = security_data.merge_market_data()
    weights = np.matrix(np.ones(7))/7
    #universal_data = security_data.get_m_score(universal_data, weights)
    universal_data.to_csv("total_data.csv", index=False)