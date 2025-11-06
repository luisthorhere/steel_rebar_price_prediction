from fastapi import APIRouter, Depends, Request
from model.predict import steel_price_prediction
from .schema import SteelRebarPriceResponse
from .dependencies import verify_api_key


router = APIRouter(prefix="/predict", tags=["Steel"])

@router.get("/steel-rebar-price/",  dependencies=[Depends(verify_api_key)])
async def steel_rebar_price():
    steel_price = steel_price_prediction()
    return steel_price