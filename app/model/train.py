from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from pandas.tseries.offsets import BDay
from pathlib import Path
from joblib import load
import pandas as pd
import joblib
import time
from ..config.config import SETTINGS
from ..api.schema import SteelRebarPriceResponse
from .utils import last_close_and_date
from ..logger.logger import logger
from ..data.get_data import (
    correlational_feautures_historical,
    steel_rebar_data,
    merge_feautures,
)


_cached_prediction = None
_cache_timestamp = 0

# --- RUTAS BASE COMO Path ---
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR.parent
MODEL_PATH = BASE_DIR / "steel_rebar_model_v2.pkl"
DATA_PATH = APP_DIR / "data" / "dataset_model_ready.csv"


def get_historical_data():
    steel_df = steel_rebar_data()
    features_df = correlational_feautures_historical()
    merge_feautures(steel_df, features_df)


def train_model_data():

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"No encuentro el dataset: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    features = ["hot_rolled_coil", "iron_ore", "usd_mxn", "coal"]
    target = "steel_rebar_next"

    faltantes = [c for c in features + [target] if c not in df.columns]
    if faltantes:
        raise KeyError(f"Faltan columnas en el dataset: {faltantes}")

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    return X_train, X_test, y_train, y_test


def train_random_forest(X_train, X_test, y_train, y_test):
    rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)


    mae = mean_absolute_error(y_test, y_pred_rf)
    mape = mean_absolute_percentage_error(y_test, y_pred_rf) * 100
    r2 = r2_score(y_test, y_pred_rf)

    logger.info("MAE RF: %.4f", mae)
    logger.info("MAPE RF: %.2f%%", mape)
    logger.info("R2 RF: %.4f", r2)


    joblib.dump({"model": rf, "r2": r2, "mape": mape}, MODEL_PATH)
    logger.info("RandomForest model saved at: %s", str(MODEL_PATH))


def predict_random_forest():
    global _cached_prediction, _cache_timestamp

    current_time = time.time()
    if _cached_prediction is not None and (current_time - _cache_timestamp) < SETTINGS.cache_ttl:
        logger.info(" Using prediccionn saved on cache (last updated  %.1f minutes)",
                    (current_time - _cache_timestamp) / 60)
        return _cached_prediction


    logger.info("Cache expired, recaclculate prediction...")

    symbols = {
        "HRC=F": "hot_rolled_coil",
        "TIO=F": "iron_ore",
        "MXN=X": "usd_mxn",
        "COAL": "coal",
    }
    feature_cols = ["hot_rolled_coil", "iron_ore", "usd_mxn", "coal"]

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"The model is not finded on the path {MODEL_PATH}.")
    model_data = load(MODEL_PATH)
    model = model_data["model"]
    mape = model_data.get("mape", None)

    values = {}
    dates = []

    for ticker, name in symbols.items():
        try:
            v, d = last_close_and_date(ticker, lookback_days=10)
            if v is None or pd.isna(v):
                raise ValueError(f"Null value for the {ticker}")
            if d is None:
                raise ValueError(f"Date null for the {ticker}")

            v = float(v)
            d = pd.to_datetime(d)

            values[name] = v
            dates.append(d)

            logger.info("%s: %.4f (último cierre %s)", name, v, d.date())
        except Exception as e:
            raise RuntimeError(f"Failure at getting the {ticker} ({name}): {e}") from e

    faltantes_en_values = [c for c in feature_cols if c not in values]
    if faltantes_en_values:
        raise KeyError(f"There are missing feautures: {faltantes_en_values}")

    X_latest = pd.DataFrame([[values[c] for c in feature_cols]], columns=feature_cols)

    last_feat_date = max(dates)
    prediction_date = (last_feat_date + BDay(1)).date()

    pred_next = float(model.predict(X_latest)[0])

    mape_confidence = round(1 - (mape / 100), 2)

    response = SteelRebarPriceResponse(
        prediction_date=str(prediction_date),
        predicted_price_usd_per_ton=round(pred_next, 2),
        model_confidence=mape_confidence,
    )

    _cached_prediction = response
    _cache_timestamp = current_time

    logger.info("Recalculated prediction, saving on cache.")
    logger.info("JSON: %s", response)

    return response

