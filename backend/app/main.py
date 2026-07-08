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
from .core.config import settings
from .core.security import verify_auth


class PrivateNetworkMiddleware:
    """Allow public web pages (GitHub Pages) to access Tailscale private network APIs.
    
    Chrome's Private Network Access policy blocks requests from public origins
    to private IP ranges (100.x.x.x = Tailscale). This header tells the browser
    that the server explicitly allows such cross-network access.
    
    Must be added AFTER CORSMiddleware so CORS preflight headers are already set.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_pna(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"access-control-allow-private-network", b"true"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_pna)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于真实案例的留学选校推荐引擎",
        dependencies=[Depends(verify_auth)],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Must be added AFTER CORSMiddleware so CORS headers are already set
    app.add_middleware(PrivateNetworkMiddleware)

    app.include_router(recommend_router)
    app.include_router(mbti_router)
    app.include_router(timeline_router)
    app.include_router(news_router)
    app.include_router(chat_router)
    app.include_router(auth_router)
    app.include_router(school_router)
    app.include_router(knowledge_router)

    return app


app = create_app()
