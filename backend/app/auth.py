# backend/app/auth.py
from fastapi import HTTPException, Query, Security
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    header_key: str | None = Security(api_key_header),
    query_key: str | None = Query(None, alias="api_key"),
) -> str:
    """Accept API key from header (X-API-Key) or query param (?api_key=).
    Query param fallback needed for SSE (EventSource can't send headers)."""
    api_key = header_key or query_key
    if not api_key or api_key != settings.app_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key
