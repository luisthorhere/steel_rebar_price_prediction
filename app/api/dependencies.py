from fastapi import Header, HTTPException, status
from .rate_limiter import check_rate_limit
from ..config.config import SETTINGS
from ..logger.logger import logger
async def verify_api_key(x_api_key: str = Header(...)):
    
    if x_api_key not in SETTINGS.api_key:
        logger.info(f"Invalid API_KEY: {x_api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    check_rate_limit(x_api_key)