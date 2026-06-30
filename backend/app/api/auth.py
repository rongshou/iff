from pydantic import BaseModel

from fastapi import APIRouter

from ..core.config import settings

router = APIRouter(prefix="/api", tags=["auth"])


class VerifyAuthCodeRequest(BaseModel):
    auth_code: str


class VerifyAuthCodeResponse(BaseModel):
    valid: bool


@router.post("/verify-auth-code", response_model=VerifyAuthCodeResponse)
def verify_auth_code(request: VerifyAuthCodeRequest):
    """
    验证授权码是否合法（由运营方分配的有效授权码列表）。
    如果 VALID_AUTH_CODES 未配置（空字符串），则跳过验证，视为合法。
    """
    raw = settings.VALID_AUTH_CODES.strip()
    if not raw:
        return VerifyAuthCodeResponse(valid=True)

    valid_codes = [c.strip() for c in raw.split(",") if c.strip()]
    return VerifyAuthCodeResponse(valid=request.auth_code in valid_codes)
