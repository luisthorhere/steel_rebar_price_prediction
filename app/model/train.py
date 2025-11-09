from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from pandas.tseries.offsets import BDay
from joblib import load
import pandas as pd
import os
import joblib
from pathlib import Path

from .utils import last_close_and_date
from ..logger.logger import logger
from ..data.get_data import (
    correlational_feautures_historical,
    steel_rebar_data,
    merge_feautures,
)

# --- RUTAS BASE COMO Path ---
BASE_DIR = Path(__file__).resolve().parent        # carpeta actual del módulo
APP_DIR = BASE_DIR.parent                         # asumiendo estructura app/<este_módulo>
MODEL_PATH = BASE_DIR / "steel_rebar_model_v2.pkl"
DATA_PATH = APP_DIR / "data" / "dataset_model_ready.csv"

def get_historical_data():
    steel_df = steel_rebar_data()
    features_df = correlational_feautures_historical()
    merge_feautures(steel_df, features_df)


def train_model_data():
    # Carga dataset
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"No encuentro el dataset: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    features = ["hot_rolled_coil", "iron_ore", "usd_mxn", "coal"]
    target = "steel_rebar_next"

    # Validaciones rápidas
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
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        random_state=42
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)

    mape = mean_absolute_percentage_error(y_test, y_pred_rf) * 100
    logger.info("MAPE RF: %.4f", mape)

    # Guarda modelo
    joblib.dump(rf, MODEL_PATH)
    logger.info("RandomForest model saved at: %s", str(MODEL_PATH))


def predict_random_forest():
    # --- Tickers y columnas de features ---
    symbols = {
        "HRC=F": "hot_rolled_coil",
        "TIO=F": "iron_ore",
        "MXN=X": "usd_mxn",
        "COAL": "coal"  # valida que exista; si no, ajusta
    }
    feature_cols = ["hot_rolled_coil", "iron_ore", "usd_mxn", "coal"]

    # 1) Modelo
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No encuentro el modelo en {MODEL_PATH}.")
    model = load(MODEL_PATH)

    # 2) Traer último cierre y fecha de cada feature
    values = {}
    dates = []

    for ticker, name in symbols.items():
        try:
            v, d = last_close_and_date(ticker, lookback_days=10)
            if v is None or pd.isna(v):
                raise ValueError(f"Valor nulo/NaN para {ticker}")
            if d is None:
                raise ValueError(f"Fecha nula para {ticker}")

            v = float(v)
            d = pd.to_datetime(d)

            values[name] = v
            dates.append(d)

            logger.info("%s: %.4f (último cierre %s)", name, v, d.date())
        except Exception as e:
            raise RuntimeError(f"Fallo al traer {ticker} ({name}): {e}") from e

    # 3) Ensamble del vector de entrada en orden correcto
    faltantes_en_values = [c for c in feature_cols if c not in values]
    if faltantes_en_values:
        raise KeyError(f"Faltan columnas de features: {faltantes_en_values}")

    X_latest = pd.DataFrame([[values[c] for c in feature_cols]], columns=feature_cols)

    # 4) Fecha de predicción = siguiente día hábil al más reciente de los features
    last_feat_date = max(dates)
    prediction_date = (last_feat_date + BDay(1)).date()

    # 5) Predicción
    pred_next = float(model.predict(X_latest)[0])

    # 6) Log y retorno
    logger.info("Resumen de predicción")
    logger.info("---------------------")
    logger.info("Último día hábil con features: %s", last_feat_date.date())
    logger.info("Día de predicción (siguiente hábil): %s", prediction_date)
    logger.info("Predicción steel rebar (USD/ton): %.2f", pred_next)

    result = {
        "prediction_date": str(prediction_date),
        "predicted_price_usd_per_ton": round(pred_next, 2),
        "currency": "USD",
        "unit": "metric ton",
        "model_confidence": "",
        "timestamp": ""
    }
    logger.info("JSON: %s", result)

    return result
