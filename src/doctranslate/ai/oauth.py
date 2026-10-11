"""Browser-based OAuth helpers for desktop provider authentication."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import secrets
import threading
import time
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser
from urllib import parse as urllib_parse, request as urllib_request

from .auth import CredentialStore, OAuthAuth


class OAuthConfigurationError(RuntimeError):
    """OAuth configuration is missing or cannot be used safely."""

    code = "oauth_config_invalid"

    def __init__(self, message: str, *, remedy: str) -> None:
        super().__init__(message)
        self.remedy = remedy


GEMINI_OAUTH_CLIENT_ID_ENV = "TRANSLATE_GEMINI_OAUTH_CLIENT_ID"
GEMINI_OAUTH_CLIENT_ID_REMEDY = (
    "Create or select a Google OAuth desktop client, then set its client ID "
    "in Gemini Configuration or in TRANSLATE_GEMINI_OAUTH_CLIENT_ID. "
    "The client ID normally ends with .apps.googleusercontent.com."
)


def resolve_gemini_oauth_client_id(client_id: str | None = None) -> str:
    """Resolve and validate a real Google OAuth client ID before browser use."""
    value = (client_id or os.environ.get(GEMINI_OAUTH_CLIENT_ID_ENV, "")).strip()
    if not value:
        raise OAuthConfigurationError(
            "Gemini OAuth client ID is not configured.",
            remedy=GEMINI_OAUTH_CLIENT_ID_REMEDY,
        )
    if not value.endswith(".apps.googleusercontent.com"):
        raise OAuthConfigurationError(
            "Gemini OAuth client ID has an invalid format.",
            remedy=GEMINI_OAUTH_CLIENT_ID_REMEDY,
        )
    return value


@dataclass(frozen=True)
class OAuthTokens:
    access_token: str
    refresh_token: str | None = None
    expires_at: float | None = None

    def valid(self) -> bool:
        return bool(self.access_token) and (
            self.expires_at is None or self.expires_at > time.time() + 60
        )


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class BrowserOAuth(OAuthAuth):
    """Small loopback OAuth client; providers supply URLs and token exchange."""

    def __init__(
        self,
        *,
        client_id: str,
        authorize_url: str,
        token_url: str,
        scopes: tuple[str, ...],
        credential_ref: str,
        store: CredentialStore,
        token_exchange=None,
        browser_open=webbrowser.open,
        timeout: float = 180,
    ) -> None:
        self.client_id = client_id
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.scopes = scopes
        self.credential_ref = credential_ref
        self.store = store
        self.token_exchange = token_exchange or self._default_exchange
        self.browser_open = browser_open
        self.timeout = timeout

    def _default_exchange(self, grant_type: str, payload: dict[str, str]) -> dict[str, object]:
        values = dict(payload)
        values["grant_type"] = (
            "authorization_code" if grant_type == "authorization_code" else "refresh_token"
        )
        req = urllib_request.Request(
            self.token_url,
            data=urllib_parse.urlencode(values).encode("ascii"),
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=self.timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
        if not isinstance(value, dict) or not value.get("access_token"):
            raise RuntimeError("OAuth token endpoint returned no access token")
        return value

    def _save(self, tokens: OAuthTokens) -> None:
        self.store.set(self.credential_ref, json.dumps({
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_at": tokens.expires_at,
        }))

    def _load(self) -> OAuthTokens | None:
        raw = self.store.get(self.credential_ref)
        if not raw:
            return None
        try:
            value = json.loads(raw)
            return OAuthTokens(value["access_token"], value.get("refresh_token"), value.get("expires_at"))
        except (TypeError, KeyError, ValueError, json.JSONDecodeError):
            return None

    def token(self, interactive: bool = False) -> str:
        current = self._load()
        if current and current.valid():
            return current.access_token
        if current and current.refresh_token:
            refreshed = self.token_exchange(
                "refresh_token",
                {"refresh_token": current.refresh_token, "client_id": self.client_id},
            )
            tokens = OAuthTokens(
                refreshed["access_token"],
                refreshed.get("refresh_token", current.refresh_token),
                time.time() + float(refreshed.get("expires_in", 3600)),
            )
            self._save(tokens)
            return tokens.access_token
        if interactive:
            self.login(True)
            current = self._load()
            if current:
                return current.access_token
        raise RuntimeError("OAuth login is required for this provider")

    def login(self, interactive: bool = True) -> None:
        if not interactive:
            raise RuntimeError("Browser OAuth requires interactive login")
        state = secrets.token_urlsafe(24)
        verifier = secrets.token_urlsafe(48)
        callback: dict[str, str] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                values = parse_qs(urlparse(self.path).query)
                callback["code"] = values.get("code", [""])[0]
                callback["state"] = values.get("state", [""])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Login received. You can close this window.")

            def log_message(self, *_args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        redirect_uri = f"http://127.0.0.1:{server.server_port}/callback"
        query = urlencode({
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": _pkce_challenge(verifier),
            "code_challenge_method": "S256",
            "access_type": "offline",
        })
        opened = self.browser_open(self.authorize_url + "?" + query)
        if opened is False:
            server.server_close()
            raise RuntimeError("Cannot open browser for OAuth login")
        deadline = time.monotonic() + self.timeout
        try:
            while time.monotonic() < deadline and "code" not in callback:
                server.timeout = min(1.0, max(0.1, deadline - time.monotonic()))
                server.handle_request()
        finally:
            server.server_close()
        if callback.get("state") != state or not callback.get("code"):
            raise RuntimeError("OAuth callback state or authorization code is invalid")
        exchanged = self.token_exchange(
            "authorization_code",
            {
                "code": callback["code"],
                "code_verifier": verifier,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
            },
        )
        self._save(OAuthTokens(
            exchanged["access_token"],
            exchanged.get("refresh_token"),
            time.time() + float(exchanged.get("expires_in", 3600)),
        ))

    def logout(self) -> None:
        self.store.delete(self.credential_ref)


class GeminiOAuth(BrowserOAuth):
    """Gemini desktop OAuth configuration; token exchange remains injectable."""

    def __init__(self, *, credential_ref: str, store: CredentialStore, token_exchange=None, **kwargs):
        super().__init__(
            client_id=kwargs.pop("client_id", os.environ.get(GEMINI_OAUTH_CLIENT_ID_ENV, "")),
            authorize_url=kwargs.pop("authorize_url", "https://accounts.google.com/o/oauth2/v2/auth"),
            token_url=kwargs.pop("token_url", "https://oauth2.googleapis.com/token"),
            scopes=kwargs.pop("scopes", ("https://www.googleapis.com/auth/generative-language",)),
            credential_ref=credential_ref,
            store=store,
            token_exchange=token_exchange,
            **kwargs,
        )

    def login(self, interactive: bool = True) -> None:
        if interactive:
            self.client_id = resolve_gemini_oauth_client_id(self.client_id)
        super().login(interactive)
