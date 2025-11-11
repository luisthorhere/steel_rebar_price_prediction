from concurrent.futures import ThreadPoolExecutor 
from pandas.tseries.offsets import BDay
from datetime import date
from pathlib import Path
import yfinance as yf
import pandas as pd
import asyncio
import joblib
import os

from ..api.schema import SteelRebarPriceResponse

base_path = os.path.dirname(__file__)

# --- RUTAS BASE COMO Path ---
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR.parent
MODEL_PATH = BASE_DIR / "steel_rebar_model_v2.pkl"
DATA_PATH = APP_DIR / "data" / "dataset_model_ready.csv"


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


def load_model(path: Path):
    """Load the trained model and metrics from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Model not found at {path}")
    data = joblib.load(path)
    return data["model"], data.get("mape", None)


def make_prediction(
    model, X_latest: pd.DataFrame, mape: float, last_feat_date: pd.Timestamp
):
    """Generate prediction and confidence from the model."""
    pred_next = float(model.predict(X_latest)[0])
    prediction_date = (last_feat_date + BDay(1)).date()
    mape_confidence = round(1 - (mape / 100), 2)
    return SteelRebarPriceResponse(
        prediction_date=str(prediction_date),
        predicted_price_usd_per_ton=round(pred_next, 2),
        model_confidence=mape_confidence,
    )


async def get_latest_features(symbols: dict[str, str], lookback_days: int = 10) -> tuple[pd.DataFrame, date]:
    """
    Fetch and validate the latest feature values from Yahoo Finance concurrently.
    Downloads all tickers in parallel using a thread pool for faster execution.
    """
    loop = asyncio.get_event_loop()
    values, dates = {}, []

    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = {
            name: loop.run_in_executor(executor, last_close_and_date, ticker, lookback_days)
            for ticker, name in symbols.items()
        }

        for name, task in tasks.items():
            v, d = await task
            if v is None or pd.isna(v):
                raise ValueError(f"Null value for {name}")
            if d is None:
                raise ValueError(f"Null date for {name}")
            values[name] = float(v)
            dates.append(pd.to_datetime(d))

    X_latest = pd.DataFrame([[values[c] for c in values.keys()]], columns=list(values.keys()))
    return X_latest, max(dates)
