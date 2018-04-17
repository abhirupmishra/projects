import numpy as np
import pandas as pd
import datetime as dt

class Portfolio(object):

    def __init__(self, rebalancing_freq = 5):
        self.rebalancing_freq = rebalancing_freq
    
    def __symbol_to_path(self, ticker):
        path = "data//"+ticker+".csv"
        return path
    
    def get_data(self, symbols, dates, addIndex=True, colname = "Adj Close"):
        """Read stock data (adjusted close) for given symbols from CSV files."""
        
        df = pd.DataFrame(index=dates)
        
        "add '000300.SS' for reference, if absent"
        if addIndex and "000300.SS" not in symbols:
            symbols = ["000300.SS"] + symbols
        
        for symbol in symbols:
            df_temp = pd.read_csv(self.__symbol_to_path(symbol), index_col='Date',
                    parse_dates=True, usecols=['Date', colname], na_values=['nan'])
            df_temp = df_temp.rename(columns={colname: symbol})
            df = df.join(df_temp)
                    
            "drop dates the Index did not trade on"
            if symbol == "000300.SS":  
                df = df.dropna(subset=["000300.SS"])
        
        df = df.fillna(method='ffill')
        df = df.fillna(method='backfill')
        df = df.fillna(10.0)
        return df
    
    def evaluate_portfolio(self, orders_df, start_date, end_date, \
                           start_val = 1000000, transaction = 0.001):
        "reading the file"
        market_cost_price = transaction
        orders = orders_df.copy()
        
        "getting the start and the end dates"
        dates = pd.date_range(start_date, end_date)
        
        "getting distinct symbols"
        syms = list(set(orders['Symbol'].tolist()))
        
        "prices and holdings val dataframe"
        prices_all = (self.get_data(syms, dates))[syms]
        portvals = pd.DataFrame(columns=['PortfolioVal'], index=prices_all.index)
        holdings = pd.DataFrame(columns=syms,index=prices_all.index)
        cash = pd.DataFrame(columns=["Cash"],index=prices_all.index)
        
        "initializing holdings, cash and portfolio values"
        holdings.iloc[0,:] = 0
        cash.ix[0,:] = start_val
        portvals.ix[0,:] = start_val
                   
        count = 0
        
        for index in holdings.index:
            order_date = str(index).split(" ")[0]
            that_days_orders = orders[orders['Date'] == order_date]
            
            "rolling over from previous day"
            if(count > 0 ):
                holdings.ix[count,:] = holdings.ix[count-1,:]
                cash.ix[count,:] = cash.ix[count-1,:]
            
            for i in that_days_orders.index:
                symbol = that_days_orders.ix[i,'Symbol']
                
                if(np.isnan(prices_all.ix[index,symbol])):
                    pass
                else:
                    "the current holding"
                    if(that_days_orders.ix[i,'Order'] == 'BUY'):
                        holdings.ix[index,symbol] += that_days_orders.ix[i,'Shares']
                        cash.ix[index] -= prices_all.ix[index,symbol]*that_days_orders.ix[i,'Shares']
                    else:
                        holdings.ix[index,symbol] -= that_days_orders.ix[i,'Shares']
                        cash.ix[index] += prices_all.ix[index,symbol]*that_days_orders.ix[i,'Shares']
                    
                    new_trade_val = abs(that_days_orders.ix[i,'Shares'])
                    total_cost = prices_all.ix[index,symbol]*new_trade_val*market_cost_price
                    cash.ix[index,0] -= total_cost
                    
            "getting the price row with updated prices"
            price_vector = np.transpose(prices_all.loc[index,:].as_matrix())
            holdings_vector = (holdings.ix[count].as_matrix()).astype(float)
            portvals.ix[index,0] = np.matmul(price_vector,holdings_vector)
                                   
            count += 1   
        
        "summing stock and cash"
        portvals = portvals['PortfolioVal'] + cash['Cash']
        return portvals
    
    def compute_statistics(self, portvals, rfr):
        
        daily_portfolio_returns  = portvals/portvals.shift(1)
        daily_portfolio_returns = daily_portfolio_returns.dropna()
        daily_portfolio_returns = daily_portfolio_returns.apply(lambda x: np.log(x))
        
        "standard deviation of returns"
        sddr = pd.Series.std(daily_portfolio_returns)
        
        "annualized daily return"
        adr = pd.Series.mean(daily_portfolio_returns)
        
        "sharpe ratio"
        sr = np.sqrt(252.0)*((adr-(rfr/252.0))/sddr)
        
        "maximum drawdown"
        maxpt=daily_portfolio_returns.iloc[0]
        mdd=0
        
        for date in daily_portfolio_returns.index:
            
            if daily_portfolio_returns[daily_portfolio_returns.index == date][0] > maxpt:
                maxpt=daily_portfolio_returns[daily_portfolio_returns.index ==date][0]
                
            if ((maxpt - daily_portfolio_returns[daily_portfolio_returns.index == date][0]) > mdd):
                mdd = maxpt - daily_portfolio_returns[daily_portfolio_returns.index == date][0]
        
        return sddr, sr, adr, mdd
        
if __name__ == '__main__':
    port = Portfolio()
    syms = list(["603799.SS","603123.SS"])
    start_date = "2015-01-01"
    end_date = "2015-12-31"
    
    dates = pd.date_range(start_date, end_date)
    data = port.get_data(syms, dates)