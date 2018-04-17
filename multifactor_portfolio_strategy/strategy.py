import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from security_data import SecurityData
from portfolio import Portfolio
import datetime as dt

class Strategy(object):
    
    def __init__(self, rebalancing_freq = 5, num_stocks = 100, beta_neutral = False, \
                 transaction_cost = 0.001, verbose = False, initial_val = 1000000, \
                 index_ticker = "000300.SS"):
        self.rebalancing_freq = rebalancing_freq
        self.num_stocks = num_stocks
        self.transaction_cost = transaction_cost
        self.verbose = verbose
        self.initial_val = initial_val
        self.capm_lookback = 100
        self.beta_neutral = beta_neutral
        self.index_ticker = index_ticker
    
    def ols_regression(self, y_val, x_val):
        """OLS Regression"""
        x_val["intercept"] = 1
        result = smf.OLS(y_val, x_val).fit()
        return result
    """end of function"""
    
    def get_m_score(self, universal_data, weights):
        """compute m-score based on the weight hyperparameteres"""
        weight_vector = np.tile(weights, (universal_data.shape[0], 1))
        universal_data["MScore"] = pd.DataFrame.sum(pd.DataFrame.multiply(universal_data.iloc[:,2:],weight_vector),axis=1)
        return universal_data
    """end of function"""
    
    """compute capm beta"""
    def compute_port_beta(self, syms, end_date, rfr = 0.0391):
        
        start_date = pd.to_datetime(end_date) - pd.tseries.offsets.BDay(self.capm_lookback + 1)
        port = Portfolio()
        
        "getting the market daata"
        dates = pd.date_range(start_date, end_date)
        
        market_data = port.get_data(syms, dates)
        
        mkt_ret = market_data.iloc[:,0]
        mkt_ret = mkt_ret.astype(float)/mkt_ret.astype(float).shift(1)
        mkt_ret = mkt_ret.dropna()
        mkt_ret = np.log(mkt_ret)
        mkt_ret = mkt_ret.to_frame()
        
        port_beta = 0
        mkt_tickers = list(market_data.columns)[1:]
        
        "getting beta value using linear regression"
        for stock in mkt_tickers:
            ret = market_data[stock]/market_data[stock].shift(1)
            ret = ret.dropna()
            ret = (np.log(ret) - rfr).to_frame()
            mkt_ret.index = ret.index
            
            results = self.ols_regression(ret, mkt_ret)
            beta = results.params[0]
            port_beta = beta + port_beta
        
        return (port_beta/self.num_stocks)
        
    
    def construct_portfolio_scores(self, combined_data_df, portfolio_date_index):
        """function to construct the portfolio. Takes input as merged fundamental data"""
        
        combined_data_df = combined_data_df.sort_values("Date")
        dates = pd.DataFrame(index=portfolio_date_index)
        rows = len(list(dates.index))
        
        port_val = self.initial_val
        
        total_portvals = pd.Series()
        portfolio = Portfolio()
        prev_holding = pd.DataFrame(columns= ["Date","Symbol","Order", "Shares"])
        
        for i in range(0,rows - self.rebalancing_freq,self.rebalancing_freq):
            date = str(dates.index[i])
            
            try:
                "running the cross-sectional regression for weights"
                if self.verbose:
                    print ("Running regression for :"+ date)
                
                subset_data = combined_data_df[combined_data_df.Date.isin([date])]
                
                x_vals = subset_data.iloc[:,4:]
                y_val = np.log(subset_data.iloc[:,3])
                result = self.ols_regression(y_val, x_vals)
                weights = result.params[:-1].as_matrix()
                
                subset_data = subset_data[["ticker", "Adj Close", "PB","PCF","PE","PS","PM","PRev","Volatility"]]
                subset_data = self.get_m_score(subset_data, weights)
                
                subset_data = subset_data.sort_values(["MScore"], ascending=False)
                subset_data = subset_data.iloc[0:self.num_stocks]
                subset_data["Date"] = date
                
                "getting the tickers to make the trade"
                orders = pd.DataFrame(columns= ["Date","Symbol","Order", "Shares"])
                orders.Symbol = subset_data.ticker
                orders.Date = date
                orders.Order = "BUY"
                orders.Shares = (port_val/self.num_stocks)/subset_data['Adj Close']
                

                "adding the old stocks to the index"
                old_stocks = list(set(prev_holding.Symbol) - set(subset_data.ticker))
                common_stocks = list(set(subset_data.ticker).intersection(prev_holding.Symbol))
                
                "clearing the old stocks, as they have to be liquidated"
                clear_order = prev_holding[prev_holding.Symbol.isin(old_stocks)]
                clear_order = clear_order[clear_order.Symbol != self.index_ticker]
                clear_order.Date = date
                clear_order.Order = "SELL"
                
                "adjusting the positions of the new order from the previous order"
                for stock in common_stocks:
                    if (stock != self.index_ticker):
                        "getting the previous holding"
                        old_holding = prev_holding.loc[prev_holding.Symbol == stock]["Shares"].iloc[0]
                        current_holding = orders.loc[orders.Symbol == stock]["Shares"].iloc[0]
                        
                        "adjusting that holding in the order and keeping record of the new holding"
                        orders.at[orders.Symbol == stock, "Shares"] = current_holding - old_holding
                        prev_holding.at[prev_holding.Symbol == stock, "Shares"] = current_holding
                    
                
                orders.Order = np.where(orders.Shares < 0, "SELL","BUY")
                orders.Shares = np.abs(orders.Shares)
                orders = orders[orders.Shares > 0]
                
                if clear_order.shape[0] > 0:
                    orders = orders.append(clear_order)
                
                start_date = date
                end_date = str(dates.index[i + self.rebalancing_freq])

                "setting the previous holding as the order"
                if (i == 0):
                    prev_holding = orders.copy()
                
                "deleting the cleared entries from the holding"                    
                prev_holding = prev_holding[~prev_holding.Symbol.isin(old_stocks)]
                
                "appending the new orders"
                x = orders[~orders.Symbol.isin(common_stocks)]
                x = x[x.Order == "BUY"]                 
                prev_holding = prev_holding.append(x)
                
                "beta neutral strategy if beta flag is true"
                if self.beta_neutral:
                    beta = self.compute_port_beta(list(subset_data.ticker),date)
                    price = portfolio.get_data([self.index_ticker],pd.date_range(date, pd.to_datetime(date) +pd.tseries.offsets.BDay(2))).iloc[0,0]
                    index_shares = port_val*beta/float(price)
                    action = "SELL"
                    
                    if prev_holding[prev_holding.Symbol == self.index_ticker].shape[0] == 0:
                        "getting the previous holding"
                        index_holding = pd.DataFrame(data = [[date, self.index_ticker, action, 0]],
                                               columns= ["Date","Symbol","Order", "Shares"])
                        prev_holding = prev_holding.append(index_holding)
                        orders.append(index_holding)
                        
                    index_shares_previous = prev_holding.loc[prev_holding.Symbol == self.index_ticker]["Shares"].iloc[0]
                    
                    orders.at[orders.Symbol == self.index_ticker, "Shares"] = (index_shares - index_shares_previous)
                    prev_holding.at[prev_holding.Symbol == self.index_ticker, "Shares"] = index_shares
                    
                "getting the timeseries of portfolio values"
                portvals = portfolio.evaluate_portfolio(orders, start_date, end_date, port_val)
                port_val = portvals[-1]
                
                total_portvals = total_portvals.append(portvals.iloc[:-1])
                
            except:
                pass
        
        return total_portvals
    """end of function"""
                
if __name__ == '__main__':
    combined_data_df = pd.read_csv("total_data.csv")
    strategy = Strategy(verbose=True, beta_neutral=True, rebalancing_freq = 10)
    
    start_date = "2015-01-01"
    end_date = "2015-06-30"
    
    data = pd.read_csv("data/000300.SS.csv")
    data = data[(data["Adj Close"] != "null") & (data.Date >= start_date) & (data.Date <= end_date)]
    data.index = data.Date
    
    subset_data = combined_data_df[combined_data_df.Date.isin(data.Date)]
    portvals  = strategy.construct_portfolio_scores(subset_data, data.index)