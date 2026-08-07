"""HTTP client for the bulk-upload benchmark: phase-timed, honest.

Uses `http.client` rather than `requests` on purpose:

* the upload body must be written from disk in chunks so a 1.95 GB rung
  is never materialised in the client's memory - the client's own
  allocation would land inside the measurement;
* the send phase and the wait-for-response phase have to be timed
  separately, which a one-call library API cannot express;
* a server that rejects mid-body (Apache 408, a proxy 413) must be
  noticed while the body is still being written, not after.

STANDING RULE, from the map: never read a status code alone. Apache
answers with its own HTML 408 after ~10 s of an idle request body, and
the platform's stall guard answers 408 as JSON. `classify_responder`
keys on the response BODY FORMAT so a finding blames the right layer.
"""

from __future__ import annotations

import http.client
import json
import select
import ssl
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

SEND_CHUNK = 1 << 20  # 1 MiB per socket write
MAX_BODY_CAPTURE = 64 * 1024

PLATFORM = "platform"  # a Django/DRF JSON answer
PROXY = "proxy"  # an Apache/nginx HTML error page
UNKNOWN = "unknown"


@dataclass
class HttpResult:
    """One HTTP exchange, with enough context to be a finding by itself."""

    method: str
    path: str
    status: int | None
    reason: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    responder: str = UNKNOWN
    connect_seconds: float = 0.0
    send_seconds: float = 0.0
    wait_seconds: float = 0.0
    read_seconds: float = 0.0
    bytes_sent: int = 0
    error: str = ""  # transport-level failure, not an HTTP status

    @property
    def total_seconds(self) -> float:
        return (
            self.connect_seconds
            + self.send_seconds
            + self.wait_seconds
            + self.read_seconds
        )

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300

    def json(self) -> dict | list | None:
        try:
            return json.loads(self.body)
        except (ValueError, TypeError):
            return None

    def summary(self) -> str:
        if self.error and self.status is None:
            return "%s %s -> TRANSPORT FAILURE %s" % (
                self.method,
                self.path,
                self.error,
            )
        return "%s %s -> %s %s [%s] %.3fs" % (
            self.method,
            self.path,
            self.status,
            self.reason,
            self.responder,
            self.total_seconds,
        )


def classify_responder(status: int | None, headers: dict, body: str) -> str:
    """Who answered: the platform, or a hop in front of it?

    Body format decides. A JSON object/array is the platform (Django and
    DRF answer JSON on every path this harness touches). An HTML document
    is a front-end server's own error page. Anything else is UNKNOWN and
    must be reported as such rather than guessed.
    """
    stripped = (body or "").lstrip()
    if stripped[:1] in "{[":
        try:
            json.loads(body)
            return PLATFORM
        except ValueError:
            pass
    lowered = stripped[:400].lower()
    if lowered.startswith("<!doctype html") or lowered.startswith("<html"):
        return PROXY
    if "<title>" in lowered and "</title>" in lowered:
        return PROXY
    content_type = ""
    for key, value in (headers or {}).items():
        if key.lower() == "content-type":
            content_type = value.lower()
    if "json" in content_type:
        return PLATFORM
    if "html" in content_type:
        return PROXY
    return UNKNOWN


class BenchClient:
    """Minimal API client for the benchmark's five calls."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 3600.0,
        insecure: bool = False,
    ):
        parts = urlsplit(base_url)
        if parts.scheme not in ("http", "https"):
            raise ValueError("base_url must be http(s): %r" % base_url)
        self.base_url = base_url.rstrip("/")
        self.scheme = parts.scheme
        self.host = parts.hostname
        self.port = parts.port
        self.token = token
        self.timeout = timeout
        self.insecure = insecure

    # -- plumbing ---------------------------------------------------------

    def _connect(self) -> http.client.HTTPConnection:
        if self.scheme == "https":
            context = ssl.create_default_context()
            if self.insecure:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            return http.client.HTTPSConnection(
                self.host, self.port or 443, timeout=self.timeout, context=context
            )
        return http.client.HTTPConnection(
            self.host, self.port or 80, timeout=self.timeout
        )

    def _finish(
        self,
        conn: http.client.HTTPConnection,
        result: HttpResult,
    ) -> HttpResult:
        wait_started = time.perf_counter()
        response = conn.getresponse()
        result.wait_seconds = time.perf_counter() - wait_started
        read_started = time.perf_counter()
        raw = response.read(MAX_BODY_CAPTURE)
        result.read_seconds = time.perf_counter() - read_started
        result.status = response.status
        result.reason = response.reason
        result.headers = {k: v for k, v in response.getheaders()}
        result.body = raw.decode("utf-8", "replace")
        result.responder = classify_responder(
            result.status, result.headers, result.body
        )
        return result

    def request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        authenticated: bool = True,
    ) -> HttpResult:
        """A small request: body (if any) is sent in one go."""
        result = HttpResult(method=method, path=path, status=None)
        conn = self._connect()
        try:
            started = time.perf_counter()
            conn.connect()
            result.connect_seconds = time.perf_counter() - started
            # NOTE: putrequest emits its own Host header. Adding a second
            # one makes the stack answer a blanket 400 (learned the hard
            # way by assets/probe_body_limit.py) - so never set it here.
            conn.putrequest(method, path, skip_accept_encoding=True)
            for key, value in (headers or {}).items():
                conn.putheader(key, value)
            if authenticated:
                if not self.token:
                    raise ValueError("no token: set OEP_BENCH_TOKEN")
                conn.putheader("Authorization", "Token %s" % self.token)
            conn.putheader("Content-Length", str(len(body or b"")))
            send_started = time.perf_counter()
            conn.endheaders(body) if body else conn.endheaders()
            result.send_seconds = time.perf_counter() - send_started
            result.bytes_sent = len(body or b"")
            return self._finish(conn, result)
        except (OSError, http.client.HTTPException) as exc:
            result.error = "%s: %s" % (type(exc).__name__, exc)
            return result
        finally:
            conn.close()

    # -- the calls the benchmark makes ------------------------------------

    def check_token(self) -> HttpResult:
        """Read-only credential check.

        `GET /api/v0/datasets/` authenticates before it authorises (DRF
        runs authentication ahead of IsAuthenticatedOrReadOnly), so a dead
        token yields 401 {"detail": "Invalid token."} and a live one 200 -
        without writing anything.
        """
        return self.request("GET", "/api/v0/datasets/")

    def create_table(
        self, table: str, columns: list[dict], constraints: list[dict] | None = None
    ) -> HttpResult:
        """Create `table` in the `sandbox` schema.

        `?is_sandbox=1` is what puts it in `sandbox`; without it the table
        is created in `data` (api/views.py, TableAPIView.put). A benchmark
        must never land in `data`.
        """
        payload = {"query": {"columns": columns, "constraints": constraints or []}}
        return self.request(
            "PUT",
            "/api/v0/tables/%s/?is_sandbox=1" % table,
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    def describe_table(self, table: str) -> HttpResult:
        return self.request("GET", "/api/v0/tables/%s/" % table)

    def drop_table(self, table: str) -> HttpResult:
        return self.request("DELETE", "/api/v0/tables/%s/" % table)

    def row_count(self, table: str) -> HttpResult:
        return self.request("GET", "/api/v0/tables/%s/rowcount" % table)

    def upload(
        self,
        table: str,
        payload_path: Path,
        delimiter: str = "comma",
        gzipped: bool = True,
        chunk_size: int = SEND_CHUNK,
        on_progress=None,
    ) -> HttpResult:
        """Stream `payload_path` into the bulk-upload endpoint.

        The file is written to the socket in chunks and never read whole.
        Between chunks the socket is polled: if the server has already
        answered (a proxy 413, an Apache 408), sending stops there and the
        answer is read, so the result records how many bytes actually went
        out before the rejection.
        """
        size = payload_path.stat().st_size
        path = "/api/v0/tables/%s/bulk-upload?delimiter=%s" % (table, delimiter)
        result = HttpResult(method="POST", path=path, status=None)
        conn = self._connect()
        try:
            started = time.perf_counter()
            conn.connect()
            result.connect_seconds = time.perf_counter() - started
            conn.putrequest("POST", path, skip_accept_encoding=True)
            if not self.token:
                raise ValueError("no token: set OEP_BENCH_TOKEN")
            conn.putheader("Authorization", "Token %s" % self.token)
            conn.putheader("Content-Type", "text/csv")
            if gzipped:
                conn.putheader("Content-Encoding", "gzip")
            conn.putheader("Content-Length", str(size))
            conn.endheaders()

            send_started = time.perf_counter()
            sent = 0
            early_answer = False
            with open(payload_path, "rb") as fh:
                while True:
                    chunk = fh.read(chunk_size)
                    if not chunk:
                        break
                    try:
                        conn.send(chunk)
                    except (OSError, http.client.HTTPException) as exc:
                        result.error = "send aborted after %d/%d bytes: %s: %s" % (
                            sent,
                            size,
                            type(exc).__name__,
                            exc,
                        )
                        early_answer = True
                        break
                    sent += len(chunk)
                    if on_progress is not None:
                        on_progress(sent, size)
                    readable, _, _ = select.select([conn.sock], [], [], 0)
                    if readable:
                        # the server answered before we finished sending
                        result.error = (
                            "server answered after %d/%d bytes sent" % (sent, size)
                        ).strip()
                        early_answer = True
                        break
            result.send_seconds = time.perf_counter() - send_started
            result.bytes_sent = sent
            try:
                return self._finish(conn, result)
            except (OSError, http.client.HTTPException) as exc:
                if early_answer and result.error:
                    result.error += " | and no response could be read: %s: %s" % (
                        type(exc).__name__,
                        exc,
                    )
                else:
                    result.error = "%s: %s" % (type(exc).__name__, exc)
                return result
        except (OSError, http.client.HTTPException, ValueError) as exc:
            result.error = "%s: %s" % (type(exc).__name__, exc)
            return result
        finally:
            conn.close()

    def probe_body_limit(self, sizes: list[tuple[str, int]]) -> list[dict]:
        """Headers-only request-body ceiling probe (folded in from
        `assets/probe_body_limit.py`).

        Sends `Content-Length` plus `Expect: 100-continue` and reads what
        comes back BEFORE any body is written: zero payload bytes cross
        the wire. Unauthenticated and aimed at a table that does not
        exist, so no code path can write anything - safe against any
        target, production included.

        100 -> the whole chain will accept a body that big
        413 -> some hop caps below this size; that hop is the ceiling
        4xx -> the app answered before any hop looked at Content-Length
        """
        path = "/api/v0/tables/does_not_exist_bench_probe/bulk-upload?delimiter=comma"
        findings = []
        for label, size in sizes:
            row = {"label": label, "declared_bytes": size}
            conn = self._connect()
            try:
                conn.timeout = min(self.timeout, 30)
                conn.putrequest("POST", path, skip_accept_encoding=True)
                conn.putheader("Content-Type", "text/csv")
                conn.putheader("Content-Length", str(size))
                conn.putheader("Expect", "100-continue")
                conn.endheaders()  # no body
                response = conn.getresponse()
                body = response.read(600).decode("utf-8", "replace").strip()
                headers = {k: v for k, v in response.getheaders()}
                row.update(
                    status=response.status,
                    reason=response.reason,
                    server=headers.get("Server", ""),
                    responder=classify_responder(response.status, headers, body),
                    body=body[:300],
                )
            except (OSError, http.client.HTTPException) as exc:
                row.update(status=None, error="%s: %s" % (type(exc).__name__, exc))
            finally:
                conn.close()
            findings.append(row)
        return findings

    def server_header(self) -> tuple[str, HttpResult]:
        """What the target says it is served by (unauthenticated GET /)."""
        result = self.request("GET", "/", authenticated=False)
        return result.headers.get("Server", ""), result
