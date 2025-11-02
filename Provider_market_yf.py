import pandas as pd
import yfinance as yf

def fetch_candles(symbol: str, interval: str = "5m", lookback: str = "2d") -> pd.DataFrame:
    df = yf.download(tickers=symbol, period=lookback, interval=interval, auto_adjust=False, progress=False)
    if not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()
    df = df.rename(columns={c: c.title() for c in df.columns})
    return df
