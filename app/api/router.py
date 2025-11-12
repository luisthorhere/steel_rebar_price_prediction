from fastapi import APIRouter, Depends

from ..model.predict import predict_random_forest
from .dependencies import verify_api_key
from ..model.train import (
    get_historical_data,
    train_random_forest,
    train_model_data,
)


router = APIRouter(prefix="/predict", tags=["Steel"])


@router.get("/steel-rebar-price/", dependencies=[Depends(verify_api_key)])
async def steel_rebar_price():
    steel_price = predict_random_forest()
    return steel_price


@router.get("/random-forest-train/")
def random_forest():
    get_historical_data()
    X_train, X_test, y_train, y_test = train_model_data()
    train_random_forest(X_train, X_test, y_train, y_test)
