from fastapi import APIRouter, Depends
from .dependencies import verify_api_key
from ..model.predict import (
    predict_xgboost
)
from ..model.train import (
    get_historical_data,
    train_random_forest,
    train_xgboost,
    train_model_data,
    train_xgboost
)


router = APIRouter(prefix="/predict", tags=["Steel"])


@router.get("/steel-rebar-price/", dependencies=[Depends(verify_api_key)])
def steel_rebar_price():
    steel_price = predict_xgboost()
    return steel_price


@router.get("/random-forest-train/", include_in_schema=False)
def random_forest():
    get_historical_data()
    X_train, X_test, y_train, y_test = train_model_data()
    train_random_forest(X_train, X_test, y_train, y_test)


@router.get("/xgboost-train/", include_in_schema=False) 
def xgboost_model():
    get_historical_data()
    X_train, X_test, y_train, y_test = train_model_data()
    train_xgboost(X_train, X_test, y_train, y_test)