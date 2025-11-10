from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
)
from pathlib import Path
import pandas as pd
import joblib


from ..logger.logger import logger
from ..data.get_data import (
    correlational_feautures_historical_parallel,
    prepare_steel_rebar_data,
    merge_feautures,
)


# --- RUTAS BASE COMO Path ---
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR.parent
MODEL_PATH = BASE_DIR / "steel_rebar_model_v2.pkl"
DATA_PATH = APP_DIR / "data" / "dataset_model_ready.csv"


def get_historical_data():
    steel_df = prepare_steel_rebar_data()
    features_df = correlational_feautures_historical_parallel()
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
