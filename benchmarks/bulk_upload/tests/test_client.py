"""Tests for the response classifier and the run's small pure helpers.

The map's standing rule is that a status code is never read alone:
Apache answers its own 408 (HTML) on an idle request body after ~10 s and
the platform's stall guard also answers 408 (JSON). If this classifier is
wrong, a rung blames the wrong layer.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from benchmarks.bulk_upload.client import (
    PLATFORM,
    PROXY,
    SEND_CHUNK,
    UNKNOWN,
    BenchClient,
    HttpResult,
    classify_responder,
    peek_early_response,
)
from benchmarks.bulk_upload.config import parse_size, rung_label
from benchmarks.bulk_upload.results import ResultRow, schema_fingerprint

APACHE_408 = (
    '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head>\n'
    "<title>408 Request Timeout</title>\n</head><body>\n"
    "<h1>Request Timeout</h1>\n</body></html>\n"
)
PLATFORM_408 = '{"reason": "Upload stalled: below 10240 bytes/second"}'


class ClassifyTests(unittest.TestCase):
    def test_apache_html_408_is_the_proxy(self):
        self.assertEqual(
            classify_responder(408, {"Server": "Apache/2.4.52"}, APACHE_408), PROXY
        )

    def test_platform_json_408_is_the_platform(self):
        self.assertEqual(
            classify_responder(408, {"Content-Type": "application/json"}, PLATFORM_408),
            PLATFORM,
        )

    def test_same_status_two_answers(self):
        proxy = classify_responder(408, {}, APACHE_408)
        platform = classify_responder(408, {}, PLATFORM_408)
        self.assertNotEqual(proxy, platform)

    def test_413_from_a_proxy_and_from_the_platform_are_distinguished(self):
        nginx = "<html>\r\n<head><title>413 Request Entity Too Large</title></head>\r\n"
        self.assertEqual(classify_responder(413, {}, nginx), PROXY)
        self.assertEqual(
            classify_responder(413, {}, '{"reason": "Upload too large"}'), PLATFORM
        )

    def test_json_array_body(self):
        self.assertEqual(classify_responder(200, {}, "[]"), PLATFORM)

    def test_content_type_is_the_fallback(self):
        self.assertEqual(
            classify_responder(500, {"Content-Type": "text/html"}, "boom"), PROXY
        )
        self.assertEqual(
            classify_responder(500, {"Content-Type": "application/json"}, ""), PLATFORM
        )

    def test_unclassifiable_says_so_rather_than_guessing(self):
        self.assertEqual(classify_responder(502, {}, "upstream gone"), UNKNOWN)

    def test_a_json_looking_body_that_is_not_json_is_not_the_platform(self):
        self.assertEqual(classify_responder(500, {}, "{not json at all"), UNKNOWN)


class SizeTests(unittest.TestCase):
    def test_decimal_and_binary_units_are_distinct(self):
        self.assertEqual(parse_size("1MB"), 10**6)
        self.assertEqual(parse_size("1MiB"), 1024**2)
        self.assertEqual(parse_size("1.95GB"), 1_950_000_000)
        self.assertEqual(parse_size("512"), 512)

    def test_unknown_unit_is_refused(self):
        with self.assertRaises(ValueError):
            parse_size("3 parsecs")

    def test_rung_labels_are_identifier_safe(self):
        self.assertEqual(rung_label("1.95GB"), "1_95gb")
        self.assertEqual(rung_label("100MB"), "100mb")


class ResultRowTests(unittest.TestCase):
    def test_derived_throughput(self):
        row = ResultRow(slice_bytes=10**7, wire_bytes=10**6, slice_rows=1000)
        row.upload_seconds = 10.0
        row.outcome = "success"
        row.compute_derived()
        self.assertEqual(row.mb_per_s_uncompressed, 1.0)
        self.assertEqual(row.mb_per_s_wire, 0.1)
        self.assertEqual(row.rows_per_s, 100.0)
        self.assertEqual(row.compress_ratio, 10.0)

    def test_derived_is_safe_without_a_measurement(self):
        row = ResultRow()
        row.compute_derived()
        self.assertEqual(row.rows_per_s, 0.0)

    def test_a_failed_rung_reports_no_throughput(self):
        """A rung refused after 1 MB of 36 MB is not a 50 GB/s result."""
        row = ResultRow(
            slice_bytes=10**8,
            wire_bytes=36 * 10**6,
            wire_bytes_sent=10**6,
            slice_rows=777,
            outcome="HTTP 413 from proxy/front-end",
        )
        row.upload_seconds = 0.002
        row.compute_derived()
        self.assertEqual(row.mb_per_s_uncompressed, 0.0)
        self.assertEqual(row.mb_per_s_wire, 0.0)
        self.assertEqual(row.rows_per_s, 0.0)
        # but the compression ratio and what actually left survive
        self.assertAlmostEqual(row.compress_ratio, 2.7778, places=3)
        self.assertEqual(row.wire_bytes_sent, 10**6)

    def test_schema_fingerprint_changes_with_the_column_typing(self):
        text = schema_fingerprint([{"name": "series", "data_type": "text"}], [])
        jsonb = schema_fingerprint([{"name": "series", "data_type": "jsonb"}], [])
        self.assertNotEqual(text, jsonb)
        self.assertEqual(
            text, schema_fingerprint([{"name": "series", "data_type": "text"}], [])
        )


class ProductionGuardTests(unittest.TestCase):
    """A write to production must be impossible without an explicit human."""

    def test_production_target_refuses_writes_by_default(self):
        from benchmarks.bulk_upload.config import TARGETS
        from benchmarks.bulk_upload.run import BenchError, guard_production

        self.assertTrue(TARGETS["prod"].is_production)
        with self.assertRaises(BenchError):
            guard_production(TARGETS["prod"], False, "create a table")

    def test_production_target_allows_writes_when_confirmed(self):
        from benchmarks.bulk_upload.config import TARGETS
        from benchmarks.bulk_upload.run import guard_production

        guard_production(TARGETS["prod"], True, "create a table")

    def test_toep_is_not_production(self):
        from benchmarks.bulk_upload.config import TARGETS
        from benchmarks.bulk_upload.run import guard_production

        self.assertFalse(TARGETS["toep"].is_production)
        guard_production(TARGETS["toep"], False, "create a table")

    def test_a_url_target_gets_a_filesystem_safe_name(self):
        from benchmarks.bulk_upload.run import resolve_target

        target = resolve_target("http://127.0.0.1:8099")
        self.assertNotIn("/", target.name)
        self.assertNotIn(":", target.name)
        self.assertEqual(target.base_url, "http://127.0.0.1:8099")

    def test_the_harness_contains_no_token_literal(self):
        """The one rule WF-03 set: no credential in any source file."""
        import pathlib
        import re as _re

        root = pathlib.Path(__file__).resolve().parents[2]
        pattern = _re.compile(r"Token\s+[A-Za-z0-9]{20,}")
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(pattern.search(text), "token literal in %s" % path)


class EarlyResponseDetectionTests(unittest.TestCase):
    """Regression cover for the deadlock in WF-14.

    A readable socket is not an answered request. On TLS 1.3 the server sends a
    NewSessionTicket immediately after the handshake, so `select()` reports the
    fd readable with no HTTP response behind it. The original client believed
    `select()`, stopped sending after one 1 MiB chunk, and then blocked forever
    in `getresponse()` while the server waited for the rest of the declared
    Content-Length. Measured against production: every upload above SEND_CHUNK
    hung; 4,224,952 bytes timed out at 240 s where curl took 1.13 s.
    """

    class _FakeSock:
        def __init__(self, behaviour):
            self.behaviour = behaviour
            self.blocking = True

        def setblocking(self, flag):
            self.blocking = flag

        def recv(self, _n):
            if isinstance(self.behaviour, Exception):
                raise self.behaviour
            return self.behaviour

    def test_tls_bookkeeping_is_not_an_answer(self):
        """SSLWantReadError means keep sending -- this is the actual bug."""
        import ssl as _ssl

        sock = self._FakeSock(_ssl.SSLWantReadError())
        self.assertEqual(peek_early_response(sock), b"")

    def test_blocking_io_error_is_not_an_answer(self):
        sock = self._FakeSock(BlockingIOError())
        self.assertEqual(peek_early_response(sock), b"")

    def test_real_bytes_are_an_answer(self):
        sock = self._FakeSock(b"HTTP/1.1 413 Payload Too Large\r\n\r\n")
        self.assertTrue(peek_early_response(sock).startswith(b"HTTP/1.1 413"))

    def test_the_socket_is_left_blocking(self):
        """A non-blocking socket left behind would corrupt the rest of the send."""
        import ssl as _ssl

        sock = self._FakeSock(_ssl.SSLWantReadError())
        peek_early_response(sock)
        self.assertTrue(sock.blocking)

    def test_an_early_response_is_parsed_from_consumed_bytes(self):
        """Once bytes are off the wire, getresponse() cannot be used."""
        raw = (
            b"HTTP/1.1 413 Payload Too Large\r\n"
            b"Content-Type: text/html\r\n"
            b"Content-Length: 22\r\n\r\n"
            b"<html>too big</html>\r\n"
        )
        client = BenchClient("https://example.invalid", token="x")
        result = HttpResult(method="POST", path="/p", status=None)
        client._finish_from_bytes(raw, result)
        self.assertEqual(result.status, 413)
        self.assertIn("too big", result.body)
        self.assertEqual(result.responder, PROXY)


class UploadOverChunkSizeTests(unittest.TestCase):
    """End-to-end over a real socket: a body larger than SEND_CHUNK must land.

    On the pre-fix client this test hangs rather than fails, which is why the
    outer timeout matters -- the bug's signature is a stall, not an exception.
    """

    def test_multi_chunk_body_is_sent_whole(self):
        import http.server
        import tempfile
        import threading

        received = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_POST(self):  # noqa: N802
                length = int(self.headers["Content-Length"])
                body = b""
                while len(body) < length:
                    body += self.rfile.read(min(65536, length - len(body)))
                received["bytes"] = len(body)
                payload = b'{"rows": 1, "event_id": 99}'
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *a):  # silence
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            size = (SEND_CHUNK * 3) + 12345  # forces four writes
            with tempfile.NamedTemporaryFile(delete=False) as fh:
                fh.write(b"x" * size)
                path = Path(fh.name)
            client = BenchClient(
                "http://127.0.0.1:%d" % server.server_address[1],
                token="test",
                timeout=60,
            )
            result = client.upload("t", path, gzipped=False)
            self.assertEqual(result.status, 201, result.error)
            self.assertEqual(result.bytes_sent, size)
            self.assertEqual(received.get("bytes"), size)
            self.assertEqual(result.responder, PLATFORM)
        finally:
            server.shutdown()
            server.server_close()
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
