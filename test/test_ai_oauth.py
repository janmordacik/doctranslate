import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai import (
    GeminiOAuth,
    MemoryCredentialStore,
    OAuthConfigurationError,
    resolve_gemini_oauth_client_id,
)


class OAuthTests(unittest.TestCase):
    def test_refresh_is_noninteractive_and_logout_deletes_tokens(self):
        store = MemoryCredentialStore()
        calls = []

        def exchange(kind, payload):
            calls.append((kind, payload))
            return {"access_token": "new-token", "expires_in": 3600}

        oauth = GeminiOAuth(
            credential_ref="gemini-oauth",
            store=store,
            token_exchange=exchange,
            browser_open=lambda _url: True,
        )
        store.set("gemini-oauth", json.dumps({
            "access_token": "old-token",
            "refresh_token": "refresh",
            "expires_at": time.time() - 1,
        }))
        self.assertEqual(oauth.token(), "new-token")
        self.assertEqual(calls[0][0], "refresh_token")
        self.assertIn('"access_token": "new-token"', store.get("gemini-oauth"))
        self.assertIn('"refresh_token": "refresh"', store.get("gemini-oauth"))
        oauth.logout()
        self.assertIsNone(store.get("gemini-oauth"))

    def test_missing_token_requires_interactive_login(self):
        oauth = GeminiOAuth(
            credential_ref="gemini-oauth",
            store=MemoryCredentialStore(),
            token_exchange=lambda *_args: {},
            browser_open=lambda _url: True,
        )
        with self.assertRaisesRegex(RuntimeError, "login"):
            oauth.token()
        with self.assertRaisesRegex(RuntimeError, "interactive"):
            oauth.login(False)

    def test_missing_client_id_is_rejected_before_browser(self):
        with patch.dict("os.environ", {}, clear=True):
            oauth = GeminiOAuth(
                credential_ref="gemini-oauth",
                store=MemoryCredentialStore(),
                browser_open=lambda _url: self.fail("browser must not open"),
            )
            with self.assertRaises(OAuthConfigurationError) as context:
                oauth.login(True)
        self.assertEqual(context.exception.code, "oauth_config_invalid")
        self.assertIn("TRANSLATE_GEMINI_OAUTH_CLIENT_ID", context.exception.remedy)

    def test_placeholder_client_id_is_rejected(self):
        with self.assertRaises(OAuthConfigurationError):
            resolve_gemini_oauth_client_id("doctranslate-desktop")

    def test_valid_client_id_can_be_resolved_from_environment(self):
        with patch.dict(
            "os.environ",
            {"TRANSLATE_GEMINI_OAUTH_CLIENT_ID": "123456.apps.googleusercontent.com"},
            clear=True,
        ):
            self.assertEqual(
                resolve_gemini_oauth_client_id(),
                "123456.apps.googleusercontent.com",
            )


if __name__ == "__main__":
    unittest.main()
