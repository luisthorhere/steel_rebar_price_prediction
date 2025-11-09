from fastapi import HTTPException, status
from datetime import datetime, timezone
from ..config.config import SETTINGS
from ..logger.logger import logger

request_counters = {}


def check_rate_limit(api_key: str):
    now = datetime.now(timezone.utc)
    window_start = now.replace(minute=0, second=0, microsecond=0)

    if api_key not in request_counters:
        request_counters[api_key] = {"window_start": window_start, "count": 0}

    data = request_counters[api_key]

    if data["window_start"] < window_start:
        data["window_start"] = window_start
        data["count"] = 0

    if data["count"] >= SETTINGS.rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded (100 requests/hour). Try again later.",
        )
    logger.info(
        f"API_KEY: {api_key} Request made during the last hour: {data['count']}"
    )
    data["count"] += 1
