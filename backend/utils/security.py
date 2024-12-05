from fastapi import HTTPException, Header
from typing import Optional

async def verify_api_key(api_key: Optional[str] = Header(None)) -> str:
    if not api_key:
        raise HTTPException(status_code=401, detail="API key is required")
    return api_key