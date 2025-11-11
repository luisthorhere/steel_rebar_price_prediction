from pathlib import Path
import time

from ..config.config import SETTINGS
from ..logger.logger import logger
from .utils import (
    get_latest_features, 
    make_prediction,
    load_model
)

# --- Base Path Routes ---
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR.parent
MODEL_PATH = BASE_DIR / "steel_rebar_model_v2.pkl"
DATA_PATH = APP_DIR / "data" / "dataset_model_ready.csv"

_cached_prediction = None
_cache_timestamp = 0

async def predict_random_forest():
    global _cached_prediction, _cache_timestamp

    current_time = time.time()
    if (
        _cached_prediction is not None
        and (current_time - _cache_timestamp) < SETTINGS.cache_ttl
    ):
        logger.info(
            "Using cached prediction (updated %.1f minutes ago)",
            (current_time - _cache_timestamp) / 60,
        )
        return _cached_prediction

    logger.info("Cache expired — recalculating prediction...")

    symbols = {
        "HRC=F": "hot_rolled_coil",
        "TIO=F": "iron_ore",
        "MXN=X": "usd_mxn",
        "COAL": "coal",
    }

    model, mape = load_model(MODEL_PATH)
    X_latest, last_feat_date = await get_latest_features(symbols)
    response = make_prediction(model, X_latest, mape, last_feat_date)

    _cached_prediction = response
    _cache_timestamp = current_time

    logger.info("Prediction recalculated and cached successfully.")
    logger.info("JSON Response: %s", response)

    return response
