"""
FastAPI dependency for auth code verification.
Reads X-Auth-Code header, validates against settings.VALID_AUTH_CODES.
"""
from fastapi import Header, HTTPException, Request

from ..core.config import settings

AUTH_HEADER = "X-Auth-Code"
AUTH_BYPASS_PATHS = {"/api/health", "/api/verify-auth-code"}


async def verify_auth(
    request: Request,
    x_auth_code: str = Header(default="", alias=AUTH_HEADER),
) -> bool:
    # Skip auth for health and verify-auth-code endpoints
    if request.url.path in AUTH_BYPASS_PATHS:
        return True

    if settings.AUTH_DISABLED:
        return True

    if not x_auth_code:
        raise HTTPException(status_code=401, detail="缺少 X-Auth-Code 请求头")

    if not settings.is_auth_code_valid(x_auth_code):
        raise HTTPException(status_code=401, detail="授权码无效")

    return True