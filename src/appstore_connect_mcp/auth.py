"""JWT bearer-token generation for the App Store Connect API.

Apple's own documented scheme: ES256-signed JWT, max 20 minute lifetime,
audience "appstoreconnect-v1". See
https://developer.apple.com/documentation/appstoreconnectapi/generating-tokens-for-api-requests
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import jwt

_AUDIENCE = "appstoreconnect-v1"
_TOKEN_LIFETIME_SECONDS = 15 * 60  # stay comfortably under Apple's 20-minute cap
_REFRESH_MARGIN_SECONDS = 60


@dataclass(frozen=True)
class AscCredentials:
    key_id: str
    issuer_id: str
    private_key_path: Path

    @classmethod
    def from_env(cls) -> "AscCredentials":
        key_id = _require_env("ASC_KEY_ID")
        issuer_id = _require_env("ASC_ISSUER_ID")
        key_path = Path(_require_env("ASC_KEY_PATH")).expanduser()
        if not key_path.is_file():
            raise FileNotFoundError(
                f"ASC_KEY_PATH points at a file that does not exist: {key_path}"
            )
        return cls(key_id=key_id, issuer_id=issuer_id, private_key_path=key_path)


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name!r}. "
            "Set ASC_KEY_ID, ASC_ISSUER_ID, and ASC_KEY_PATH before starting the server."
        )
    return value


class TokenProvider:
    """Caches a signed JWT and re-signs it shortly before it would expire."""

    def __init__(self, credentials: AscCredentials) -> None:
        self._credentials = credentials
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get_token(self) -> str:
        now = time.time()
        if self._token is None or now >= self._expires_at - _REFRESH_MARGIN_SECONDS:
            self._token = self._sign_new_token(now)
            self._expires_at = now + _TOKEN_LIFETIME_SECONDS
        return self._token

    def _sign_new_token(self, issued_at: float) -> str:
        private_key = self._credentials.private_key_path.read_text()
        payload = {
            "iss": self._credentials.issuer_id,
            "iat": int(issued_at),
            "exp": int(issued_at + _TOKEN_LIFETIME_SECONDS),
            "aud": _AUDIENCE,
        }
        headers = {"kid": self._credentials.key_id, "alg": "ES256", "typ": "JWT"}
        return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
