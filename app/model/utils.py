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
STEEL_PATH = APP_DIR / "data" /  "steel_rebar_data.csv"



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


def get_latest_features(symbols: dict[str, str], lookback_days: int = 10) -> tuple[pd.DataFrame, date]:
    """
    Fetch and validate the latest feature values from Yahoo Finance sequentially (synchronous version).
    Downloads each ticker one by one.
    """
    values, dates = {}, []

    for ticker, name in symbols.items():
        v, d = last_close_and_date(ticker, lookback_days)
        if v is None or pd.isna(v):
            raise ValueError(f"Null value for {name}")
        if d is None:
            raise ValueError(f"Null date for {name}")
        values[name] = float(v)
        dates.append(pd.to_datetime(d))

    X_latest = pd.DataFrame([[values[c] for c in values.keys()]], columns=list(values.keys()))
    return X_latest, max(dates)


def build_latest_row(symbols: dict[str, str],
                     last_feat_date: pd.Timestamp,
                     feature_names: list[str]) -> pd.DataFrame:
    """
    Arma el vector de features EXACTO usado en entrenamiento:
    - drivers del día más reciente disponible (<= last_feat_date)
    - lags/medias del steel_rebar calculados desde el CSV histórico
    """
    # 1) Drivers desde Yahoo (ya los tienes en get_latest_features)
    X_drivers, _ = get_latest_features(symbols)   # columnas: hot_rolled_coil, iron_ore, usd_mxn, coal

    # 2) Lags/MA de steel_rebar desde tu CSV histórico
    steel = pd.read_csv(STEEL_PATH, parse_dates=["Date"])
    steel = (steel.rename(columns={"Price": "steel_rebar"})
                  .dropna(subset=["Date"])
                  .sort_values("Date")
                  .set_index("Date"))

    # Solo datos hasta la fecha de features
    steel_cut = steel.loc[:last_feat_date].copy()
    if len(steel_cut) < 7:
        raise ValueError("Histórico de steel_rebar insuficiente para calcular lags/MA.")

    steel_cut["steel_lag1"] = steel_cut["steel_rebar"].shift(1)
    steel_cut["steel_lag2"] = steel_cut["steel_rebar"].shift(2)
    steel_cut["steel_lag3"] = steel_cut["steel_rebar"].shift(3)
    steel_cut["steel_ma3"]  = steel_cut["steel_rebar"].rolling(3, min_periods=1).mean()
    steel_cut["steel_ma7"]  = steel_cut["steel_rebar"].rolling(7, min_periods=1).mean()

    last_row = steel_cut.iloc[-1][["steel_lag1","steel_lag2","steel_lag3","steel_ma3","steel_ma7"]]

    # 3) Ensambla una sola fila con todo
    row = {**X_drivers.iloc[0].to_dict(), **last_row.to_dict()}
    X_latest_full = pd.DataFrame([row])

    # 4) Reordenar/validar columnas al orden del modelo
    missing = [c for c in feature_names if c not in X_latest_full.columns]
    if missing:
        raise ValueError(f"Faltan columnas para inferencia: {missing}")

    X_latest_full = X_latest_full.reindex(columns=feature_names)

    # Asegura finitos
    if X_latest_full.isna().any().any():
        raise ValueError(f"NaN en vector de inferencia: {X_latest_full.isna().sum().to_dict()}")

    return X_latest_full