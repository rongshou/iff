"""
FastAPI dependency for auth code verification.
Reads X-Auth-Code header, validates against settings.VALID_AUTH_CODES.
Supports trial mode for /api/chat: first request with X-Trial-Id bypasses auth,
second request exhausts the trial and returns 401.
"""
from fastapi import Header, HTTPException, Request

from ..core.config import settings
from ..core.database import get_connection

AUTH_HEADER = "X-Auth-Code"
AUTH_BYPASS_PATHS = {"/api/health", "/api/verify-auth-code"}

# ── Trial session table ──────────────────────────────────────────────

TRIAL_TABLE = "trial_sessions"
TRIAL_CREATE_SQL = f"""CREATE TABLE IF NOT EXISTS {TRIAL_TABLE} (
    trial_id TEXT PRIMARY KEY,
    chat_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);"""


def ensure_trial_table() -> None:
    """Ensure trial_sessions table exists (idempotent)."""
    with get_connection() as conn:
        conn.execute(TRIAL_CREATE_SQL)
        conn.commit()


# ── Auth dependency ──────────────────────────────────────────────────


async def verify_auth(
    request: Request,
    x_auth_code: str = Header(default="", alias=AUTH_HEADER),
    x_trial_id: str = Header(default="", alias="X-Trial-Id"),
) -> bool:
    # CORS preflight: OPTIONS requests are handled by CORSMiddleware
    # before route handlers, but FastAPI global dependencies may still run.
    # Skip auth for all OPTIONS (browser preflight) requests.
    if request.method == "OPTIONS":
        return True

    # Skip auth for health and verify-auth-code endpoints
    if request.url.path in AUTH_BYPASS_PATHS:
        return True

    if settings.AUTH_DISABLED:
        return True

    # ── Trial mode for /api/chat ──────────────────────────────────
    # If no X-Auth-Code is provided on the chat endpoint, fall back to
    # trial mode.  The first call with a given X-Trial-Id is allowed;
    # the second call returns 401 with trial_exhausted.
    if request.url.path.startswith("/api/chat") and not x_auth_code:
        if not x_trial_id:
            raise HTTPException(
                status_code=401,
                detail="缺少 X-Auth-Code 或 X-Trial-Id 请求头",
            )

        ensure_trial_table()
        from ..core.database import get_db

        with get_db() as conn:
            row = conn.execute(
                "SELECT chat_count FROM trial_sessions WHERE trial_id = ?",
                (x_trial_id,),
            ).fetchone()

            if row is None:
                # First trial request: insert with chat_count=1, allow
                conn.execute(
                    "INSERT INTO trial_sessions (trial_id, chat_count) VALUES (?, 1)",
                    (x_trial_id,),
                )
                conn.commit()
                return True

            if row["chat_count"] == 1:
                # Second trial request: exhausted, bump count and reject
                conn.execute(
                    "UPDATE trial_sessions SET chat_count = 2 WHERE trial_id = ?",
                    (x_trial_id,),
                )
                conn.commit()
                raise HTTPException(
                    status_code=401,
                    detail={"trial_exhausted": True, "detail": "试用次数已用完，请登录"},
                )

            # chat_count >= 2: already exhausted
            raise HTTPException(
                status_code=401,
                detail={"trial_exhausted": True, "detail": "试用次数已用完，请登录"},
            )

    # ── Normal auth code check ────────────────────────────────────
    if not x_auth_code:
        raise HTTPException(status_code=401, detail="缺少 X-Auth-Code 请求头")

    if not settings.is_auth_code_valid(x_auth_code):
        raise HTTPException(status_code=401, detail="授权码无效")

    return True