"""
PayPlus HTTP client helper.

Thin httpx-based wrapper for PayPlus REST API.
Handles base URL selection (sandbox/prod) and auth headers.
No business logic — just HTTP transport.
"""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class PayPlusClientError(Exception):
    """Raised on non-2xx responses from PayPlus API."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"PayPlus API error {status_code}: {message}")


# Base URLs per PayPlus docs
_BASE_URLS = {
    "sandbox": "https://restapidev.payplus.co.il",
    "prod": "https://restapi.payplus.co.il",
}


class PayPlusClient:
    """HTTP client for PayPlus REST API."""

    def __init__(
        self,
        env: str = "sandbox",
        api_key: str = "",
        secret_key: str = "",
        timeout: int = 15,
    ):
        self.env = env
        self.api_key = api_key
        self.secret_key = secret_key
        self.timeout = timeout
        self.base_url = _BASE_URLS.get(env, _BASE_URLS["sandbox"])

    def _build_headers(self) -> dict[str, str]:
        """
        Build auth headers per PayPlus docs.
        Primary: Authorization header with JSON-encoded credentials.
        This is the single place to change if sandbox rejects this format.
        """
        return {
            "Content-Type": "application/json",
            "Authorization": json.dumps({
                "api_key": self.api_key,
                "secret_key": self.secret_key,
            }),
        }

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        POST JSON to PayPlus API and return parsed response.
        Raises PayPlusClientError on non-2xx responses.
        """
        url = f"{self.base_url}{path}"
        headers = self._build_headers()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            logger.error("PayPlus HTTP transport error: %s", exc)
            raise PayPlusClientError(0, f"Transport error: {exc}") from exc

        if response.status_code >= 400:
            # Log safely — truncate response to avoid leaking sensitive data
            body_preview = response.text[:500] if response.text else "(empty)"
            logger.error(
                "PayPlus API error",
                extra={
                    "status_code": response.status_code,
                    "path": path,
                    "response_preview": body_preview,
                },
            )
            raise PayPlusClientError(response.status_code, body_preview)

        try:
            return response.json()
        except Exception as exc:
            raise PayPlusClientError(
                response.status_code,
                f"Invalid JSON response: {response.text[:200]}",
            ) from exc
