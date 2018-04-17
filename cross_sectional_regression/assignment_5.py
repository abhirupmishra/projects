# -*- coding: utf-8 -*-
"""
@author: Abhirup Mishra
@GTID: 903262755
@Descrption: assignment-5
"""

import pandas as pd
import pandas_datareader as web
import numpy as np
import datetime as dt
from scipy import log
import statsmodels.formula.api as smf
import statsmodels.api as sm

class security:
    def __init__(self, tickers_df):
        self.source = "quandl"
        self.tickers_df = tickers_df

    def get_security_list(self):
        sec_list = list()
        rows = self.tickers_df.shape[0]
        for row in range(rows):
            elem = tuple(self.tickers_df.iloc[row])
            sec_list.append(elem)
        return sec_list

def get_stock_data(ticker, sd, ed):
    """ download stock data from exernal source, inputs: ticker symbol, start date & end date returns dataframe of prices """
    source = "yahoo"
    col = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    data = web.DataReader(ticker,source,sd,ed)
    return data[col]
        
def identify_firms(df, filter_criteria = 500*(10**6)):
    #removing n/a values
    df = df[df.MarketCap != "n/a"]
    
    #removing the "$" sign
    df.MarketCap = df.MarketCap.str.replace('$', '')
    df.MarketCap = (df.MarketCap.replace(r'[MB]+$', '', regex=True).astype(float) * \
               df.MarketCap.str.extract(r'[\d\.]+([MB]+)', expand=False)
               .fillna(1)
               .replace(['M','B'], [10**6, 10**9]).astype(float))
    
    #filtering the crieteria
    df = df[df.MarketCap >= filter_criteria]
    return df

def linear_regression(y, x):
    x['intercept'] = 1
    model = smf.OLS(y,x).fit()
    return model

if __name__ == "__main__":
    nyse_tickers = pd.read_csv("tickers_nyse.csv")
    nasdaq_tickers = pd.read_csv("tickers_nasd.csv")
    
    "dropping the dummmy last column"
    nyse_tickers = nyse_tickers.iloc[:,0:-1]
    nasdaq_tickers = nasdaq_tickers.iloc[:,0:-1]
    
    "filtering the firms whose market-cap > $500M"
    nyse_tickers = identify_firms(nyse_tickers)          
    nasdaq_tickers = identify_firms(nasdaq_tickers)
    
    "Securities Class"
    sec_nyse = security(nyse_tickers)
    sec_nasdaq = security(nasdaq_tickers)
    exception_list = list()
    
    sd = dt.datetime(2000,1,1)
    ed = dt.datetime.today()
    
    stock_data_combined = pd.DataFrame()
    
    symbols = list(set(list(nasdaq_tickers.Symbol) + list(nyse_tickers.Symbol)))
    
    
    for symbol in symbols:
        try:
            stock_data = get_stock_data(symbol,sd,ed)
            stock_data['pm_1D'] = stock_data['Adj Close']/stock_data['Adj Close'].shift(1)
            stock_data['pm_5D'] = stock_data['Adj Close']/stock_data['Adj Close'].shift(5)
            stock_data['pm_22D'] = stock_data['Adj Close']/stock_data['Adj Close'].shift(22)
            
            stock_data['Ticker'] = symbol
            stock_data['MA_5'] = stock_data['Adj Close'].rolling(5).mean().shift(1)
            stock_data['MA_22'] = stock_data['Adj Close'].rolling(22).mean().shift(1)
            stock_data['MA_200'] = stock_data['Adj Close'].rolling(200).mean().shift(1)
            stock_data['pm_68D_lag'] = stock_data['Adj Close'].shift(1)/stock_data['Adj Close'].shift(69)
            stock_data['pm_22D_lag'] = stock_data['Adj Close'].shift(1)/stock_data['Adj Close'].shift(23)
            stock_data['pm_5D_lag'] = stock_data['Adj Close'].shift(1)/stock_data['Adj Close'].shift(6)
            stock_data = stock_data.dropna()
            
            "appending the stock data"
            stock_data_combined = stock_data_combined.append(stock_data)
        except Exception as e:
            print(str(e))
            exception_list.append(symbol)
            
    stock_data_combined.to_csv("stock_data_combined.csv")
    
    
    y = pd.read_csv("stock_data_combined.csv", index_col=0)
    
    "subsetting for year"
    
    x_ = y[y.index == '2017-04-06'][["MA_5","MA_22", "MA_200", "pm_68D_lag","pm_22D_lag", "pm_5D_lag"]] 
    x_['pm_68D_lag'] = log(x_['pm_68D_lag'])
    x_['pm_22D_lag'] = log(x_['pm_22D_lag'])
    x_['pm_5D_lag'] = log(x_['pm_5D_lag'])
    
    needed_y = ["pm_1D", "pm_5D","pm_22D"]
    
    
    for cols in needed_y:
        print("Regression for :" + cols)
        y_ = y[y.index == '2017-04-06'][cols]
        y_ = log(y_)
            
        results = linear_regression(y_,x_)
        print(results.summary())

    num_days = 90
    business_days = 60
    
    t1 = dt.datetime(2016,6,1)
    t2 = dt.datetime(2017,7,1)
    times = [t1,t2]
    
    coeffs_df = pd.DataFrame()
    t_values_df = pd.DataFrame()
    
    count = 1
    for time in times:
        
        date_index = pd.date_range(time, time + dt.timedelta(days=num_days), freq="b")[0:business_days]
        
        for d in range(0,date_index.shape[0]):
            date = (date_index[d]).strftime('%Y-%m-%d')
            
            x_ = y[y.index == date][["MA_5","MA_22", "MA_200", "pm_68D_lag","pm_22D_lag", "pm_5D_lag"]]
            
            "subsetting the data"
            for cols in needed_y:
                try:
                    y_ = y[y.index == date][cols]
                    y_ = log(y_)
                    results = linear_regression(y_,x_)
                    t_values = results.pvalues
                    
                    res = results.params
                    
                    res = res.set_value("y_val",cols)
                    res = res.set_value("date",date)
                    res = res.set_value("set",count)
                    
                    t_values = t_values.set_value("y_val",cols)
                    t_values = t_values.set_value("date",date)
                    t_values = t_values.set_value("set",count)
                    
                    coeffs_df = coeffs_df.append(res, ignore_index=True)
                    t_values_df = t_values_df.append(t_values, ignore_index=True)
                
                except Exception as e:
                    pass
        count = count + 1
    
    "exporting to csv"
    results_df = coeffs_df.groupby(['set','y_val']).mean()
    results_df.to_csv("results.csv")
    
    t_values_df.to_csv("t_values.csv", index=False)