import time
import uuid
import logging
from contextvars import ContextVar
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.logging_config import setup_logging
from app.routers import health, user, public, auth, checkout, webhooks, admin, access, upload
from app.context import request_id_ctx

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request_id_ctx.set(req_id)
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add Request ID to response headers
        response.headers["X-Request-Id"] = req_id
        
        # Log the request (structured)
        logger.info(
            "Request processed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency": round(process_time, 4)
            }
        )
        return response

app = FastAPI(
    title="Iron Mind API",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENV != "prod" else None,
    redoc_url=None,
    servers=[
        {"url": "http://localhost:8080", "description": "Local Docker"}
    ]
)



# Custom Middleware
# app.add_middleware(RequestIdMiddleware)

# CORS
# Using regex for robust matching of localhost/127.0.0.1


# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    settings.FRONTEND_ORIGIN
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "X-Debug-Uid", "X-Debug-Admin", "X-Request-Id"],
    expose_headers=["X-Debug-Uid", "X-Debug-Admin", "X-Request-Id"]
)

# Routers

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(public.router, tags=["Public"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(user.router, tags=["User"])
app.include_router(access.router, prefix="/access", tags=["Access"])
app.include_router(checkout.router, tags=["Checkout"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])

@app.get("/")
async def root():
    return {"message": "Iron Mind API", "docs": "/docs" if settings.ENV != "prod" else "disabled"}
