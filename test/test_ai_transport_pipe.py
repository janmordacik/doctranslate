import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from doctranslate.ai.transport import SubprocessHttpTransport


class _LargeResponseHandler(BaseHTTPRequestHandler):
    response_text = "ok"

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        body = json.dumps({"message": {"content": self.response_text}}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


class SubprocessTransportPipeTests(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), _LargeResponseHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)

    def test_large_child_response_does_not_deadlock(self):
        _LargeResponseHandler.response_text = "x" * 200_000
        try:
            result = SubprocessHttpTransport().request(
                "POST", self.url(), payload={}, timeout=5
            )
        finally:
            _LargeResponseHandler.response_text = "ok"
        self.assertEqual(len(result.body["message"]["content"]), 200_000)

    def url(self):
        return f"http://127.0.0.1:{self.server.server_port}/chat"


if __name__ == "__main__":
    unittest.main()
