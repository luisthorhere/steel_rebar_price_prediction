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
    correlational_feautures_historical,
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
    features_df = correlational_feautures_historical()
    merge_feautures(steel_df, features_df)


def train_model_data():
    # load data
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing path to load the dataset: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    if "steel_rebar" not in df.columns:
        raise KeyError("Column 'steel_rebar' not found in dataset_model_ready.csv")

    # Lags (-1, -2 y -3 days)
    df["steel_lag1"] = df["steel_rebar"].shift(1)
    df["steel_lag2"] = df["steel_rebar"].shift(2)
    df["steel_lag3"] = df["steel_rebar"].shift(3)

    # Rolling averages (smooth out noise)
    df["steel_ma3"] = df["steel_rebar"].rolling(3, min_periods=1).mean()
    df["steel_ma7"] = df["steel_rebar"].rolling(7, min_periods=1).mean()

    base_features = ["hot_rolled_coil", "iron_ore", "usd_mxn", "coal"]
    inertia_feats = ["steel_lag1", "steel_lag2", "steel_lag3", "steel_ma3", "steel_ma7"]
    target = "steel_rebar_next"

    missing_cols = [c for c in base_features + [target, "steel_rebar"] if c not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing columns in the dataset: {missing_cols}")

    # Remove the first day that has nan
    df = df.dropna(subset=[target, "steel_lag1"]) 

    features = base_features + inertia_feats
    X = df[features]
    y = df[target]

    # Split train data and test
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    return X_train, X_test, y_train, y_test


def train_random_forest(X_train, X_test, y_train, y_test):
    rf = RandomForestRegressor(
        n_estimators=600, max_depth=15,
        min_samples_split=3, min_samples_leaf=2,
        max_features="sqrt", random_state=42, n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred_rf)
    mape = mean_absolute_percentage_error(y_test, y_pred_rf) * 100
    r2 = r2_score(y_test, y_pred_rf)

    logger.info("MAE RF: %.4f", mae)
    logger.info("MAPE RF: %.2f%%", mape)
    logger.info("R2 RF: %.4f", r2)

    joblib.dump(
        {"model": rf, "r2": r2, "mape": mape, "features": list(X_train.columns)},
        MODEL_PATH
    )
    logger.info("RandomForest model saved at: %s", str(MODEL_PATH))