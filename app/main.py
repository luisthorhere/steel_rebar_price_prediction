from fastapi import FastAPI, Response
from datetime import datetime, timezone
from app.api.router import router as steel_rebar_price


app = FastAPI(
    title="Steel Rebar Price Predictor",
    description="API to predice the steel rebar price.",
    version="1.0.0"
)

# Include routers
app.include_router(steel_rebar_price)

@app.get("/")
def root():
    return {
        "service": "Steel Rebar Price Predictor",
        "version": "1.0",
        "documentation_url": "http://127.0.0.1:8009/docs",
        "data_sources": [
            "https://www.investing.com/commodities/steel-rebar-historical-data",
            "Yahoo Finance",
        ],
        "last_model_update": datetime(2025, 10, 15, tzinfo=timezone.utc).isoformat()
    }