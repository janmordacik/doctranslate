import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from doctranslate.ai import GeminiOAuth, MemoryCredentialStore


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


if __name__ == "__main__":
    unittest.main()
