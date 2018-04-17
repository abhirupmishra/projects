"""MLT: Utility code."""

import pandas as pd
import matplotlib.pyplot as plt

def get_data(crsp, symbols, dates, addSPY=True, colname = 'PRC'):
    """Read stock data (adjusted close) for given symbols from CSV files."""
    df = pd.DataFrame(index=dates)
    if addSPY and "78462F10" not in symbols:  # add SPY for reference, if absent
        symbols = ["78462F10"] + list(symbols)

    for symbol in symbols:
        df_temp =crsp[crsp.CUSIP == symbol][['DATE', 'PRC']]
        df_temp.index = df_temp.DATE
        df_temp = df_temp.drop("DATE",axis=1)
        df_temp = df_temp.rename(columns={colname: symbol})
        df = df.join(df_temp)
        if symbol == '78462F10':  # drop dates SPY did not trade
            df = df.dropna(subset=["78462F10"])

    return df

def plot_data(df, title="Stock prices", xlabel="Date", ylabel="Price"):
    """Plot stock prices with a custom title and meaningful axis labels."""
    ax = df.plot(title=title, fontsize=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.show()
