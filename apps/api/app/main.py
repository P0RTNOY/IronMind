import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.logging_config import setup_logging
from app.routers import health, user, public, auth, checkout, webhooks, admin, access, upload, content, admin_vimeo, admin_payments, admin_activity
from app.middleware.request_id import RequestIdMiddleware

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.is_prod:
        missing = []
        critical_vars = [
            ("PAYPLUS_API_KEY", settings.PAYPLUS_API_KEY),
            ("PAYPLUS_SECRET_KEY", settings.PAYPLUS_SECRET_KEY),
            ("PUBLIC_WEBHOOK_BASE_URL", settings.PUBLIC_WEBHOOK_BASE_URL)
        ]
        if settings.VIMEO_VERIFY_ENABLED:
            critical_vars.append(("VIMEO_ACCESS_TOKEN", settings.VIMEO_ACCESS_TOKEN))
            
        for name, val in critical_vars:
            if not val or val == "http://localhost:8080":
                missing.append(name)
                
        if missing:
            raise RuntimeError(f"Missing critical production secrets: {', '.join(missing)}")
    
    yield

app = FastAPI(
    title="Iron Mind API",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENV != "prod" else None,
    redoc_url=None,
    servers=[
        {"url": "http://localhost:8080", "description": "Local Docker"}
    ],
    lifespan=lifespan
)



# Custom Middleware
app.add_middleware(RequestIdMiddleware)

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
app.include_router(content.router, prefix="/content", tags=["Content"])
app.include_router(admin_vimeo.router, prefix="/admin/vimeo", tags=["Admin Vimeo"])
app.include_router(admin_payments.router, prefix="/admin/payments", tags=["Admin Payments"])
app.include_router(admin_activity.router, prefix="/admin", tags=["Admin Activity"])

# Dev-only routers (never mounted in prod)
if settings.ENV != "prod":
    from app.routers import dev_seed
    app.include_router(dev_seed.router, prefix="/admin/dev", tags=["Admin Dev"])

@app.get("/")
async def root():
    return {"message": "Iron Mind API", "docs": "/docs" if settings.ENV != "prod" else "disabled"}
