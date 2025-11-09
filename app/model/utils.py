import yfinance as yf
import pandas as pd
import os

base_path = os.path.dirname(__file__)

def last_close_and_date(ticker: str, lookback_days: int = 10):
    """
    Devuelve (ultimo_cierre, fecha_ultimo_cierre) para un ticker.
    Mira hacia atrás 'lookback_days' días por si hoy no hay datos (fin de semana/feriado).
    """
    df = yf.download(ticker, period=f"{lookback_days}d", interval="1d", progress=False)[["Close"]]
    if df.empty:
        raise ValueError(f"Yahoo Finance no regresó datos para {ticker} en {lookback_days}d.")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df = df.dropna()
    if df.empty:
        raise ValueError(f"Sin cierres válidos para {ticker}.")
    last_date = df.index[-1]
    last_val = float(df["Close"].iloc[-1])
    return last_val, last_date