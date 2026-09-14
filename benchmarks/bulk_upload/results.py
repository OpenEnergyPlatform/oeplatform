"""The results file: one row per rung attempt, append-only.

Failures get a row too. A 413/408/429/500 is a measurement, not an
absence of one, and the row carries what it takes to tell a proxy's
refusal from the platform's: the status, who answered, the server
header, the bytes that made it out and the response body itself.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path

#: server-side phase timings (slice 8) are logged on the host, not
#: returned to the client; a rung says so rather than dropping the column
SERVER_TIMINGS_UNAVAILABLE = "n/a client-side (host log: oeplatform.bulk_upload)"


@dataclass
class ResultRow:
    run_id: str = ""
    timestamp_utc: str = ""
    target: str = ""
    base_url: str = ""
    arm: str = ""
    rung: str = ""
    table: str = ""
    schema: str = "sandbox"
    delimiter: str = "comma"
    source_file: str = ""
    schema_fingerprint: str = ""  # rungs with different fingerprints do not compare
    # slice
    target_bytes: int = 0
    slice_bytes: int = 0
    slice_rows: int = 0
    slice_rewritten: bool = False
    slice_passes: int = 1
    slice_seconds: float = 0.0
    slice_verified: str = ""
    # transport
    gzip_level: str = ""
    wire_bytes: int = 0  # what the payload weighs
    wire_bytes_sent: int = 0  # what actually left the client
    compress_seconds: float = 0.0
    compress_ratio: float = 0.0
    # phases (client side)
    connect_seconds: float = 0.0
    send_seconds: float = 0.0
    wait_seconds: float = 0.0
    read_seconds: float = 0.0
    upload_seconds: float = 0.0
    rung_wall_seconds: float = 0.0
    # outcome
    http_status: str = ""
    responder: str = ""
    server_header: str = ""
    rows_reported: str = ""
    event_id: str = ""
    id_min: str = ""
    id_max: str = ""
    rowcount_after: str = ""
    # derived
    mb_per_s_uncompressed: float = 0.0
    mb_per_s_wire: float = 0.0
    rows_per_s: float = 0.0
    # lifecycle
    table_created: bool = False
    table_dropped: bool = False
    drop_verified: str = ""
    # provenance
    server_timings: str = SERVER_TIMINGS_UNAVAILABLE
    outcome: str = ""
    error: str = ""
    response_body: str = ""
    notes: str = ""
    detail_file: str = ""

    def compute_derived(self) -> None:
        """Throughput exists only where a load actually completed.

        A rung that was refused mid-body moved a fraction of its payload
        in a fraction of the time; dividing one by the other invents a
        headline number out of a failure. Those cells stay 0 and
        `wire_bytes_sent` carries what really went out.
        """
        if self.wire_bytes and self.slice_bytes:
            self.compress_ratio = round(self.slice_bytes / self.wire_bytes, 4)
        if self.outcome != "success" or self.upload_seconds <= 0:
            self.mb_per_s_uncompressed = 0.0
            self.mb_per_s_wire = 0.0
            self.rows_per_s = 0.0
            return
        self.mb_per_s_uncompressed = round(
            self.slice_bytes / self.upload_seconds / 1e6, 3
        )
        self.mb_per_s_wire = round(self.wire_bytes / self.upload_seconds / 1e6, 3)
        self.rows_per_s = round(self.slice_rows / self.upload_seconds, 1)


FIELD_NAMES = [f.name for f in fields(ResultRow)]


def schema_fingerprint(columns: list, constraints: list) -> str:
    """Short hash of the exact table definition a rung was loaded into.

    Two rungs are only comparable if this matches - the column typing
    decision changes what is being measured, not just how it is stored.
    """
    blob = json.dumps(
        {"columns": columns, "constraints": constraints}, sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_row(path: Path, row: ResultRow) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists() or path.stat().st_size == 0
    with open(path, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELD_NAMES)
        if is_new:
            writer.writeheader()
        data = asdict(row)
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.replace("\r", " ").replace("\n", " ")[:2000]
        writer.writerow(data)


def write_detail(directory: Path, run_id: str, payload: dict) -> Path:
    """Full, untruncated record of one rung - bodies, headers, config."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("%s.json" % run_id)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path
