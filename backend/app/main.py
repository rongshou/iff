from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send

from .api.recommend import router as recommend_router
from .api.mbti import router as mbti_router
from .api.timeline import router as timeline_router
from .api.news import router as news_router
from .api.chat import router as chat_router
from .api.auth import router as auth_router
from .api.school import router as school_router
from .api.knowledge import router as knowledge_router
from .api.favorites import router as favorites_router
from .core.config import settings
from .core.security import ensure_trial_table, verify_auth


class PrivateNetworkMiddleware:
    """Handle Chrome Private Network Access preflight requests.
    
    Chrome's PNA policy blocks public pages (GitHub Pages) from accessing
    private network APIs (Tailscale 100.x.x.x). This middleware intercepts
    OPTIONS preflight requests with the PNA header and returns proper CORS
    headers before Starlette's CORSMiddleware rejects them.
    
    Must be OUTERMOST (added first) to run before CORSMiddleware.
    """
    PNA_HEADER_REQUEST = b"access-control-request-private-network"
    PNA_HEADER_RESPONSE = b"access-control-allow-private-network"
    
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check if this is a PNA preflight request
        headers = dict(scope.get("headers", []))
        is_preflight = scope["method"] == "OPTIONS" and headers.get(self.PNA_HEADER_REQUEST) == b"true"
        
        if not is_preflight:
            # Pass through: add PNA header to all responses
            async def send_with_pna(message):
                if message["type"] == "http.response.start":
                    msg_headers = list(message.get("headers", []))
                    msg_headers.append((self.PNA_HEADER_RESPONSE, b"true"))
                    message["headers"] = msg_headers
                await send(message)
            await self.app(scope, receive, send_with_pna)
            return

        # Handle PNA preflight: return 200 with all required CORS+PNA headers
        origin = headers.get(b"origin", b"*").decode()
        req_method = headers.get(b"access-control-request-method", b"GET, POST, OPTIONS").decode()
        req_headers = headers.get(b"access-control-request-headers", b"*").decode()

        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"access-control-allow-origin", origin.encode()),
                (b"access-control-allow-methods", req_method.encode()),
                (b"access-control-allow-headers", req_headers.encode()),
                (self.PNA_HEADER_RESPONSE, b"true"),
                (b"access-control-max-age", b"86400"),
                (b"content-length", b"0"),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": b"",
        })


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于真实案例的留学选校推荐引擎",
        dependencies=[Depends(verify_auth)],
    )

    # CORSMiddleware added first (inner layer) — handles standard CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # PrivateNetworkMiddleware added last (outer layer) — intercepts
    # PNA preflight BEFORE CORSMiddleware can reject it.
    # Starlette add_middleware wraps: last added = outermost.
    app.add_middleware(PrivateNetworkMiddleware)

    # Initialize trial sessions table for first-request-free trial mode
    ensure_trial_table()

    app.include_router(recommend_router)
    app.include_router(mbti_router)
    app.include_router(timeline_router)
    app.include_router(news_router)
    app.include_router(chat_router)
    app.include_router(auth_router)
    app.include_router(school_router)
    app.include_router(knowledge_router)
    app.include_router(favorites_router)

    return app


app = create_app()
