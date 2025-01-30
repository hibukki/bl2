from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import time
from typing import Optional
class GPT0Settings(BaseModel):
    response_delay_seconds: float

router = APIRouter()
_settings: Optional[GPT0Settings] = None

def configure_router(response_delay_seconds: float = 0):
    global _settings
    _settings = GPT0Settings(response_delay_seconds=response_delay_seconds)
    return router

def get_settings() -> GPT0Settings:
    if _settings is None:
        raise HTTPException(status_code=500, detail="Settings not configured")
    return _settings

@router.get("/gpt0")
def gpt0(settings: GPT0Settings = Depends(get_settings)):
    if settings.response_delay_seconds > 0:
        time.sleep(settings.response_delay_seconds)
    return "hello world" 