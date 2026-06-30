from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.recommend import router as recommend_router
from .api.mbti import router as mbti_router
from .api.timeline import router as timeline_router
from .api.news import router as news_router
from .api.chat import router as chat_router
from .api.auth import router as auth_router
from .api.school import router as school_router
from .core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于真实案例的留学选校推荐引擎",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(recommend_router)
    app.include_router(mbti_router)
    app.include_router(timeline_router)
    app.include_router(news_router)
    app.include_router(chat_router)
    app.include_router(auth_router)
    app.include_router(school_router)

    return app


app = create_app()
