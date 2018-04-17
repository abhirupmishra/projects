import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from security_data import SecurityData
from portfolio import Portfolio
from strategy import Strategy
import datetime as dt

if __name__ == '__main__':
    combined_data_df = pd.read_csv("total_data.csv")
    strategy = Strategy(verbose=True, beta_neutral=False, rebalancing_freq = 10)
    portfolio = Portfolio()
    
    """out-sample testing"""
    start_date = "2014-11-01"
    end_date = "2015-07-31"
    
    data = pd.read_csv("data/000300.SS.csv")
    data = data[(data["Adj Close"] != "null") & (data.Date >= start_date) & (data.Date <= end_date)]
    data.index = data.Date
    
    subset_data = combined_data_df[combined_data_df.Date.isin(data.Date)]
    portvals  = strategy.construct_portfolio_scores(subset_data, data.index)
    
    sddr, sr, adr, mdd = portfolio.compute_statistics(portvals, 0.039)
    
    """in-sample testing"""
    start_date = "2013-10-01"
    end_date = "2014-10-31"
    
    data = pd.read_csv("data/000300.SS.csv")
    data = data[(data["Adj Close"] != "null") & (data.Date >= start_date) & (data.Date <= end_date)]
    data.index = data.Date
    
    subset_data = combined_data_df[combined_data_df.Date.isin(data.Date)]
    portvals  = strategy.construct_portfolio_scores(subset_data, data.index)    
    sddr, sr, adr, mdd = portfolio.compute_statistics(portvals, 0.039)