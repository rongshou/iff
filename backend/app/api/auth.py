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
    AUTH_DISABLED=true 时（开发模式）任何授权码均视为合法；
    否则使用 is_auth_code_valid 进行恒定时间比较，fail-closed。
    """
    if settings.AUTH_DISABLED:
        return VerifyAuthCodeResponse(valid=True)

    return VerifyAuthCodeResponse(valid=settings.is_auth_code_valid(request.auth_code))
