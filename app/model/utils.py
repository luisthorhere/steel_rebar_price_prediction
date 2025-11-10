import yfinance as yf
import pandas as pd
import os

base_path = os.path.dirname(__file__)


def last_close_and_date(ticker: str, lookback_days: int = 10):
    """
    Returns (last_close, last_close_date) for a given ticker.
    Looks back 'lookback_days' days in case there is no data for today (weekend/holiday).
    """
    df = yf.download(ticker, period=f"{lookback_days}d", interval="1d", progress=False)[
        ["Close"]
    ]
    if df.empty:
        raise ValueError(
            f"Yahoo Finance did not return data for {ticker} in the past {lookback_days} days."
        )
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.dropna()
    if df.empty:
        raise ValueError(f"No valid closing prices found for {ticker}.")
    last_date = df.index[-1]
    last_val = float(df["Close"].iloc[-1])
    return last_val, last_date
