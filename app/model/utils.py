from pandas.tseries.offsets import BDay
from datetime import date
from pathlib import Path
import yfinance as yf
import pandas as pd
import joblib
import os

from ..api.schema import SteelRebarPriceResponse

base_path = os.path.dirname(__file__)


# --- RUTAS BASE COMO Path ---
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR.parent
MODEL_PATH = BASE_DIR / "steel_rebar_model_v2.pkl"
DATA_PATH = APP_DIR / "data" / "dataset_model_ready.csv"
STEEL_PATH = APP_DIR / "data" / "steel_rebar_data.csv"


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
    last_close_date = df.index[-1]
    last_close_value = float(df["Close"].iloc[-1])
    return last_close_value, last_close_date


def load_model(path):
    saved = joblib.load(path)
    model = saved["model"]
    mape = saved.get("mape", None)
    feat_names = saved.get("features", getattr(model, "feature_names_in_", None))
    return model, mape, feat_names


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


def get_latest_features(
    symbols: dict[str, str], lookback_days: int = 10
) -> tuple[pd.DataFrame, date]:
    """
    Fetch and validate the latest feature values from Yahoo Finance sequentially (synchronous version).
    Downloads each ticker one by one.
    """
    feature_values = {}
    feature_dates = []

    for ticker_symbol, feature_name in symbols.items():
        latest_value, latest_date = last_close_and_date(ticker_symbol, lookback_days)
        if latest_value is None or pd.isna(latest_value):
            raise ValueError(f"Null value for {feature_name}")
        if latest_date is None:
            raise ValueError(f"Null date for {feature_name}")

        feature_values[feature_name] = float(latest_value)
        feature_dates.append(pd.to_datetime(latest_date))

    X_latest = pd.DataFrame(
        [[feature_values[c] for c in feature_values.keys()]],
        columns=list(feature_values.keys()),
    )
    return X_latest, max(feature_dates)


def build_latest_row(
    symbols: dict[str, str], last_feat_date: pd.Timestamp, feature_names: list[str]
) -> pd.DataFrame:
    """
    Builds the EXACT feature vector used during training:
    - Includes the most recent available drivers (<= last_feat_date)
    - Computes steel_rebar lags and moving averages from the historical CSV file
    """
    # Get data from yahoo finance
    X_drivers, _ = get_latest_features(
        symbols
    )  # columns: hot_rolled_coil, iron_ore, usd_mxn, coal

    # 2) Load steel reabar hsitorical data
    steel = pd.read_csv(STEEL_PATH, parse_dates=["Date"])
    steel = (
        steel.rename(columns={"Price": "steel_rebar"})
        .dropna(subset=["Date"])
        .sort_values("Date")
        .set_index("Date")
    )

    # Use only data available up to the most recent feature date
    steel_cut = steel.loc[:last_feat_date].copy()
    if len(steel_cut) < 7:
        raise ValueError("Insufficient historical steel_rebar data to calculate lag and moving average features.")

    steel_cut["steel_lag1"] = steel_cut["steel_rebar"].shift(1)
    steel_cut["steel_lag2"] = steel_cut["steel_rebar"].shift(2)
    steel_cut["steel_lag3"] = steel_cut["steel_rebar"].shift(3)
    steel_cut["steel_ma3"] = steel_cut["steel_rebar"].rolling(3, min_periods=1).mean()
    steel_cut["steel_ma7"] = steel_cut["steel_rebar"].rolling(7, min_periods=1).mean()

    # Take the last date data
    last_row = steel_cut.iloc[-1][
        ["steel_lag1", "steel_lag2", "steel_lag3", "steel_ma3", "steel_ma7"]
    ]

    # 3) Create a latest row data
    row = {**X_drivers.iloc[0].to_dict(), **last_row.to_dict()}
    X_latest_full = pd.DataFrame([row])

    # 4) Reorder columns in the same way as during model training
    missing = [c for c in feature_names if c not in X_latest_full.columns]
    if missing:
        raise ValueError(f"Faltan columnas para inferencia: {missing}")

    X_latest_full = X_latest_full.reindex(columns=feature_names)

    # Ensure finite values
    if X_latest_full.isna().any().any():
        raise ValueError(
            f"NaN en vector de inferencia: {X_latest_full.isna().sum().to_dict()}"
        )

    return X_latest_full
