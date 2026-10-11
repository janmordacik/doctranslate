import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from doctranslate.ai.contracts import BackendError
from doctranslate.ai.transport import SubprocessHttpTransport


class _ResponseHandler(BaseHTTPRequestHandler):
    delay = 0

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        if self.delay:
            time.sleep(self.delay)
        body = json.dumps({"message": {"content": "ok"}}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


class SubprocessTransportTests(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), _ResponseHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)

    def url(self):
        return f"http://127.0.0.1:{self.server.server_port}/chat"

    def test_request_returns_child_response(self):
        result = SubprocessHttpTransport().request(
            "POST", self.url(), payload={"text": "hello"}, timeout=5
        )
        self.assertEqual(result.body["message"]["content"], "ok")

    def test_wall_clock_timeout_terminates_child(self):
        _ResponseHandler.delay = 2
        reasons = []
        try:
            with self.assertRaises(BackendError) as caught:
                SubprocessHttpTransport(on_abort=reasons.append).request(
                    "POST", self.url(), payload={}, timeout=0.1
                )
        finally:
            _ResponseHandler.delay = 0
        self.assertEqual(caught.exception.code, "request_timeout")
        self.assertEqual(reasons, ["timeout"])


if __name__ == "__main__":
    unittest.main()
