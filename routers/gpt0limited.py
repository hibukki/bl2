from fastapi import APIRouter, HTTPException, Response, Depends
from typing import Optional
from pydantic import BaseModel
import requests

class GPT0LimitedSettings(BaseModel):
    bandwidth_limit_bytes: int
    base_url: str
    remaining_bandwidth_bytes: int

router = APIRouter()
_settings: Optional[GPT0LimitedSettings] = None

def configure_router(bandwidth_limit_bytes: int = 1000, base_url: str = "http://localhost:8000"):
    global _settings
    _settings = GPT0LimitedSettings(
        bandwidth_limit_bytes=bandwidth_limit_bytes,
        base_url=base_url,
        remaining_bandwidth_bytes=bandwidth_limit_bytes
    )
    return router

def get_settings() -> GPT0LimitedSettings:
    if _settings is None:
        raise HTTPException(status_code=500, detail="Settings not configured")
    return _settings

@router.get("/limited-gpt0")
def limited_gpt0(settings: GPT0LimitedSettings = Depends(get_settings)):
    # Get the actual data from gpt0 endpoint
    try:
        response = requests.get(f"{settings.base_url}/gpt0")
        response.raise_for_status()
        gpt0_completion = response.text
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch from GPT0: {str(e)}")

    gpt0_completion_utf8 = gpt0_completion.encode('utf-8')
    response_size_bytes = len(gpt0_completion_utf8)

    settings.remaining_bandwidth_bytes -= response_size_bytes
    if settings.remaining_bandwidth_bytes < 0:
        raise HTTPException(status_code=429, detail="Bandwidth limit exceeded")
    
    return Response(content=gpt0_completion_utf8) 