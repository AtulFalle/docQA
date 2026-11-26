"""Request context middleware: request id, structured access log."""

import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from docqa_core.logging import bind_log_context, clear_log_context, get_logger

REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware:
    """Pure ASGI middleware binding request metadata to the log context."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle one ASGI call, tagging HTTP requests with a request id."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        incoming = headers.get(REQUEST_ID_HEADER.lower().encode(), b"").decode("latin-1")
        request_id = incoming or uuid.uuid4().hex
        clear_log_context()
        bind_log_context(request_id=request_id, method=scope["method"], path=scope["path"])
        status_code = 500
        start = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            get_logger("docqa_ai_api.access").info(
                "request.completed",
                status_code=status_code,
                duration_ms=round((time.perf_counter() - start) * 1000, 2),
            )
            clear_log_context()
