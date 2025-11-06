from fastapi import FastAPI, Response
from api.router import router as steel_rebar_price
from datetime import datetime, timezone

app = FastAPI(
    title="Residency Car Access API",
    description="API to manage vehicle access for residents, guests, and service providers.",
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
            "London Metal Exchange (LME)",
            "Trading Economics",
            "FRED (Federal Reserve Economic Data)"
        ],
        "last_model_update": datetime(2025, 10, 15, tzinfo=timezone.utc).isoformat()
    }