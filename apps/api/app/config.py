import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    PROJECT_ID: str = "iron-mind-dev"
    ENV: str = "dev"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    
    # Auth
    ADMIN_UIDS: List[str] = []
    FIREBASE_ADMIN_SDK_JSON_BASE64: str = ""
    FIREBASE_PROJECT_ID: str = ""

    @field_validator("FIREBASE_PROJECT_ID", mode="before")
    def default_firebase_project_id(cls, v: str, info) -> str:
        if v:
            return v
        return info.data.get("PROJECT_ID", "")

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_FUNDAMENTALS_ONE_TIME: str = ""
    STRIPE_PRICE_ID_MEMBERSHIP_MONTHLY: str = ""
    
    CHECKOUT_SUCCESS_URL: str = "http://localhost:5173/success?session_id={CHECKOUT_SESSION_ID}"
    CHECKOUT_CANCEL_URL: str = "http://localhost:5173/cancel"
    
    # GCS
    GCS_BUCKET_NAME: Optional[str] = None
    GCS_PUBLIC_BASE_URL: str = "https://storage.googleapis.com"
    SIGNED_URL_TTL_SECONDS: int = 900  # 15 minutes

    # Video
    VIDEO_PROVIDER: str = "vimeo"
    VIMEO_EMBED_BASE_URL: str = "https://player.vimeo.com/video"
    VIMEO_VERIFY_ENABLED: bool = False
    VIMEO_ACCESS_TOKEN: str = ""
    VIMEO_REQUIRED_EMBED_ORIGINS: List[str] = ["ironmind.app", "www.ironmind.app"]
    VIMEO_API_BASE_URL: str = "https://api.vimeo.com"
    VIMEO_VERIFY_TIMEOUT_SECONDS: int = 15
    
    CURRENCY_DEFAULT: str = "ils"
    APP_VERSION: str = "0.0.1"

    # Email
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Iron Mind <noreply@ironmind.app>"

    # Payments
    PAYMENTS_PROVIDER: str = "stub"
    PAYMENTS_REPO: str = "firestore"

    # PayPlus
    PAYPLUS_ENV: str = "sandbox"                          # "sandbox" | "prod"
    ENABLE_PAYPLUS: bool = False
    PAYPLUS_API_KEY: str = ""
    PAYPLUS_SECRET_KEY: str = ""
    PAYPLUS_PAYMENT_PAGE_UID_ONE_TIME: str = ""
    PAYPLUS_PAYMENT_PAGE_UID_SUBSCRIPTION: str = ""
    PAYPLUS_WEBHOOK_VERIFY_MODE: str = "enforce"          # "enforce" | "log_only"
    PAYPLUS_TIMEOUT_SECONDS: int = 15
    PUBLIC_WEBHOOK_BASE_URL: str = "http://localhost:8080"
    WEBHOOK_RATE_LIMIT_ENABLED: bool = True
    
    # Phase 6.2A Additions
    PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS: bool = True
    PAYPLUS_RECURRING_ENABLED: bool = False
    PAYPLUS_PAYLOAD_REDACT_KEYS: List[str] = [
        "email", "phone", "full_name", "first_name", 
        "last_name", "card", "cc", "pan", "cvv", "exp", "address"
    ]

    # Dev Seed
    SEED_DEBUG_UID: str = ""

    @property
    def is_prod(self) -> bool:
        return self.ENV == "prod"

    @field_validator("ADMIN_UIDS", mode="before")
    def parse_admin_uids(cls, v) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v_str = v.strip()
            if not v_str:
                return []
            import json
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(uid).strip() for uid in parsed if str(uid).strip()]
                except Exception:
                    pass
            return [uid.strip() for uid in v_str.split(",") if uid.strip()]
        return []


    @field_validator("VIMEO_REQUIRED_EMBED_ORIGINS", mode="before")
    def parse_required_embed_origins(cls, v) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip():
                return []
            return [orig.strip() for orig in v.split(",") if orig.strip()]
        return []

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
