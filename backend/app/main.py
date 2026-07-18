"""
Application entrypoint.

Creates the FastAPI app instance and mounts versioned API routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup / shutdown hooks (DB warm-up, client init, etc. come later)."""
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "environment": settings.app_env}

    return application


app = create_app()
