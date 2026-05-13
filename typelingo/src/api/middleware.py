"""HTTP middleware for TypeLingo API."""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every HTTP request.

    * Binds ``request_id`` into structlog's context vars so every log
      line emitted during that request automatically includes it.
    * Sets an ``X-Request-ID`` response header so callers can correlate
      logs with their own traces.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: object) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            # call_next is typed as RequestResponseEndpoint in Starlette
            response: Response = await call_next(request)  # type: ignore[operator]
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-ID"] = request_id
        return response
