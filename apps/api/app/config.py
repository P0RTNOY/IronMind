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
    
    CURRENCY_DEFAULT: str = "ils"
    APP_VERSION: str = "0.0.1"

    # Email
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Iron Mind <noreply@ironmind.app>"

    @field_validator("ADMIN_UIDS", mode="before")
    def parse_admin_uids(cls, v) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip():
                return []
            return [uid.strip() for uid in v.split(",") if uid.strip()]
        return []

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
