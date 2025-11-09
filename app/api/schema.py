from pydantic import BaseModel, Field
from datetime import date, datetime, timezone


class SteelRebarPriceResponse(BaseModel):
    prediction_date: date | None = Field(default_factory=date.today)
    predicted_price_usd_per_ton: float = Field(default=None)
    currency: str = Field(default="USD")
    unit: str = Field(default="metric ton")
    model_confidence: float = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
