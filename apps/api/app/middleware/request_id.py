import logging
import time
import uuid
from starlette.types import ASGIApp, Receive, Scope, Send

from app.context import request_id_ctx

logger = logging.getLogger(__name__)

class RequestIdMiddleware:
    """
    ASGI Middleware that guarantees an X-Request-Id is generated, stored in ContextVars,
    injected into the response headers, and that every HTTP request is logged with its duration.
    This runs outside FastAPI's ExceptionMiddleware, natively handling crashes too.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        req_id = ""
        for name, value in scope.get("headers", []):
            if name.lower() == b"x-request-id":
                req_id = value.decode("latin1")
                break

        if not req_id:
            req_id = str(uuid.uuid4())

        request_id_ctx.set(req_id)

        start_time = time.time()
        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                headers = list(message.get("headers", []))
                if not any(k.lower() == b"x-request-id" for k, _ in headers):
                    headers.append((b"x-request-id", req_id.encode("latin1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            process_time = time.time() - start_time
            # Log the structured request summary
            logger.info(
                "Request processed",
                extra={
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status_code": status_code,
                    "latency": round(process_time, 4),
                },
            )
