from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import RequestIDMiddleware
from src.api.v1.assess import router as assess_router
from src.api.v1.auth import router as auth_router
from src.api.v1.health import router as health_router
from src.api.v1.sessions import router as sessions_router
from src.api.v1.users import router as users_router
from src.api.v1.vocab import router as vocab_router
from src.config import settings
from src.observability.logging import configure_logging
from src.websocket.handler import router as ws_router


def create_app() -> FastAPI:
    configure_logging(settings.debug)
    app = FastAPI(title="TypeLingo", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(vocab_router, prefix="/api/v1")
    app.include_router(assess_router, prefix="/api/v1")
    app.include_router(ws_router)
    return app


app = create_app()
