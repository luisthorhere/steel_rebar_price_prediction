from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.api.router import router as steel_rebar_price
from app.logger.logger import logger
from app.model.predict import predict_random_forest

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Setting up app...")
    predict_random_forest()
    logger.info("Cache updated for predictions")
    logger.info("Startup completed successfully")
    yield


app = FastAPI(
    title="Steel Rebar Price Predictor",
    description="API to predict the steel rebar price.",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(steel_rebar_price)

@app.get("/")
def root(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "service": "Steel Rebar Price Predictor",
        "version": "1.0",
        "documentation_url": f"{base}/docs",
        "data_sources": [
            "https://www.investing.com/commodities/steel-rebar-historical-data",
            "Yahoo Finance",
        ],
        "last_model_update": datetime(2025, 10, 15, tzinfo=timezone.utc).isoformat()
    }