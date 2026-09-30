"""Command line for the bulk-upload benchmark.

    # nothing leaves the machine: slice, compress, print the payloads
    python -m benchmarks.bulk_upload.run --target toep --arm narrow \
        --rungs 1MB,10MB --dry-run

    # is the credential live, and may it create and drop in sandbox?
    export OEP_BENCH_TOKEN=...            # never a literal in this repo
    python -m benchmarks.bulk_upload.run --target toep --check-auth

    # what body size will the chain accept? (unauthenticated, zero payload)
    python -m benchmarks.bulk_upload.run --target prod --probe-body-limit

    # the real thing: a staircase that stops at the first hard limit
    python -m benchmarks.bulk_upload.run --target toep --arm fat \
        --rungs 1MB,10MB,100MB,1GB,1.95GB --results path/to/results.csv

Production is write-protected: any call that writes to a target marked
`is_production` refuses unless `--i-am-a-human-confirming-production` is
given, because the map keeps prod writes human-in-the-loop.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import sys
import tempfile
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlsplit

from benchmarks.bulk_upload import config as cfg
from benchmarks.bulk_upload import results as res
from benchmarks.bulk_upload import slicing
from benchmarks.bulk_upload.client import PLATFORM, PROXY, BenchClient, HttpResult

TOKEN_ENV = "OEP_BENCH_TOKEN"
TABLE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,49}$")
DEFAULT_RESULTS = Path("benchmarks/results/bulk_upload_results.csv")
PROBE_SIZES = [
    ("100 MiB", 100 * 1024**2),
    ("1 GiB", 1024**3),
    ("1.90 GiB (the fat file)", 2_040_220_631),
    ("2 GiB", 2 * 1024**3),
    ("10 GiB (BULK_UPLOAD_MAX_BYTES default)", 10 * 1024**3),
]


class BenchError(RuntimeError):
    """A run cannot proceed - configuration, not a measurement."""


def log(message: str) -> None:
    print(message, flush=True)


def read_token(required: bool = True) -> str | None:
    token = os.environ.get(TOKEN_ENV, "").strip()
    if not token:
        if required:
            raise BenchError(
                "%s is not set. The harness never contains a token literal; "
                "export the account's API token (OEP user settings -> Show "
                "token) into %s for this shell only." % (TOKEN_ENV, TOKEN_ENV)
            )
        return None
    return token


def table_name(arm: str, rung: str, stamp: str) -> str:
    name = "bench_%s_%s_%s" % (arm, cfg.rung_label(rung), stamp)
    if not TABLE_NAME_RE.match(name):
        raise BenchError(
            "generated table name %r is not a valid OEP identifier "
            "(^[a-z][a-z0-9_]{0,49}$)" % name
        )
    return name


def slice_path(work_dir: Path, arm: cfg.Arm, target_bytes: int) -> Path:
    tag = "%s_%d%s%s%s" % (
        arm.name,
        target_bytes,
        "_drop-" + "-".join(arm.drop_columns) if arm.drop_columns else "",
        "_renum" if arm.renumber_id else "",
        "_rep" if arm.repeat else "",
    )
    return work_dir / ("slice_%s.csv" % tag)


def make_slice(
    arm: cfg.Arm, target_bytes: int, work_dir: Path, use_cache: bool
) -> tuple[slicing.SliceResult, float, bool]:
    """Slice (or reuse) a rung. Returns (result, seconds, was_cached)."""
    dest = slice_path(work_dir, arm, target_bytes)
    meta = dest.with_name(dest.name + ".meta.json")
    if use_cache and dest.exists() and meta.exists():
        data = json.loads(meta.read_text(encoding="utf-8"))
        if data.get("actual_bytes") == dest.stat().st_size:
            data["path"] = dest
            return slicing.SliceResult(**data), 0.0, True
    started = time.perf_counter()
    result = slicing.slice_csv(
        arm.source,
        dest,
        target_bytes,
        delimiter=arm.csv_delimiter,
        drop_columns=arm.drop_columns,
        renumber_id=arm.renumber_id,
        repeat=arm.repeat,
    )
    seconds = time.perf_counter() - started
    payload = asdict(result)
    payload["path"] = str(result.path)
    meta.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return result, seconds, False


def compress(source: Path, dest: Path, level: int) -> tuple[int, float]:
    """gzip a slice to disk, streaming. Returns (bytes, seconds).

    Pre-compressing rather than compressing on the fly is deliberate:
    gzip -6 runs at roughly 20 MB/s on this data, so compressing inside
    the upload would fold ~100 s of client CPU into a 1.9 GB transfer
    measurement and quietly become the bottleneck being measured.
    """
    started = time.perf_counter()
    with open(source, "rb") as src, open(dest, "wb") as raw:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, compresslevel=level, mtime=0
        ) as out:
            shutil.copyfileobj(src, out, length=1 << 20)
    seconds = time.perf_counter() - started
    return dest.stat().st_size, seconds


def guard_production(target: cfg.Target, confirmed: bool, what: str) -> None:
    if target.is_production and not confirmed:
        raise BenchError(
            "refusing to %s against production (%s). Prod writes are "
            "human-in-the-loop on this map: re-run with "
            "--i-am-a-human-confirming-production if a human really is "
            "driving." % (what, target.base_url)
        )


def describe_http(result: HttpResult) -> str:
    if result.status is None:
        return "TRANSPORT FAILURE: %s" % result.error
    tail = " %s" % result.error if result.error else ""
    return "%s %s [answered by: %s]%s :: %s" % (
        result.status,
        result.reason,
        result.responder,
        tail,
        result.body[:300].replace("\n", " "),
    )


# --- preflights ----------------------------------------------------------


def probe_body_limit(client: BenchClient) -> list[dict]:
    """Declare a huge body, send none of it, see who objects.

    Reading the result on the Apache + mod_wsgi stack the OEP actually
    runs on: `100 Continue` is NOT what acceptance looks like there.
    Apache does not answer the Expect header up front, it waits for the
    body, and after ~10 s of silence answers its own HTML **408**. So

      413            -> a hop caps below this size; THAT is the ceiling
      408 from proxy -> the declared length was accepted, the body simply
                        never came (this probe never sends one)
      4xx from platform -> the app answered before any hop looked at
                        Content-Length

    A run of 408s with no 413 anywhere therefore means: no proxy body cap
    up to the largest size probed.
    """
    log("\n== request-body ceiling (headers only, no payload, unauthenticated)")
    findings = client.probe_body_limit(PROBE_SIZES)
    log("%-42s %-8s %-9s %s" % ("declared size", "status", "answered", "server"))
    for row in findings:
        log(
            "%-42s %-8s %-9s %s %s"
            % (
                row["label"],
                row.get("status", "ERR"),
                row.get("responder", "-"),
                row.get("server", ""),
                row.get("error", ""),
            )
        )
    capped = [r for r in findings if r.get("status") == 413]
    reached = [r for r in findings if r.get("status") is not None]
    if capped:
        log("  VERDICT: body ceiling below %s (first 413)" % capped[0]["label"])
    elif reached:
        log(
            "  VERDICT: no 413 at any probed size - no proxy body cap up to %s"
            % reached[-1]["label"]
        )
    else:
        log("  VERDICT: nothing was reached; see the errors above")
    return findings


def check_auth(
    client: BenchClient, target: cfg.Target, confirmed: bool, keep: bool = False
) -> dict:
    """Preflight: token live? sandbox create/drop permitted? body ceiling?"""
    report: dict = {"target": target.name, "base_url": target.base_url}

    server, root = client.server_header()
    log("\n== target identity")
    log("  base url      : %s" % target.base_url)
    log("  Server header : %s" % (server or "(none sent)"))
    log("  GET /         : %s" % describe_http(root)[:120])
    report["server_header"] = server
    report["root"] = asdict(root)

    log("\n== token (read-only check: GET /api/v0/datasets/)")
    token_result = client.check_token()
    log("  %s" % describe_http(token_result))
    report["token_check"] = asdict(token_result)
    if token_result.status == 401:
        raise BenchError(
            "token rejected (401). Nothing further can be checked. Get the "
            "live value from OEP user settings -> Show token; do NOT reset "
            "the token, OEP issues one per user and a reset is destructive."
        )
    if not token_result.ok:
        raise BenchError(
            "unexpected answer to the token check: %s" % describe_http(token_result)
        )
    log("  token is LIVE")

    report["probe"] = probe_body_limit(client)

    log("\n== sandbox round-trip (create -> confirm -> drop -> confirm gone)")
    guard_production(target, confirmed, "create a table")
    name = table_name("auth", "probe", time.strftime("%Y%m%d%H%M%S"))
    columns = [
        {"name": "id", "data_type": "bigint"},
        {"name": "value", "data_type": "text"},
    ]
    steps: dict[str, dict] = {}
    created = client.create_table(name, columns)
    steps["create"] = asdict(created)
    log("  create %s: %s" % (name, describe_http(created)))
    if not created.ok:
        report["sandbox_roundtrip"] = {"verdict": "CREATE DENIED", "steps": steps}
        log("  VERDICT: this account may NOT create tables in sandbox here.")
        return report
    confirm = client.describe_table(name)
    steps["confirm"] = asdict(confirm)
    log("  confirm      : %s" % describe_http(confirm)[:160])
    if keep:
        report["sandbox_roundtrip"] = {"verdict": "CREATED, KEPT", "steps": steps}
        return report
    dropped = client.drop_table(name)
    steps["drop"] = asdict(dropped)
    log("  drop         : %s" % describe_http(dropped)[:160])
    gone = client.describe_table(name)
    steps["confirm_gone"] = asdict(gone)
    log("  confirm gone : %s" % describe_http(gone)[:160])
    verdict = (
        "CREATE+DROP OK"
        if created.ok and dropped.ok and gone.status == 404
        else "INCOMPLETE - inspect the steps"
    )
    log("  VERDICT: %s" % verdict)
    report["sandbox_roundtrip"] = {"verdict": verdict, "steps": steps}
    return report


# --- one rung ------------------------------------------------------------


def run_rung(
    client: BenchClient,
    target: cfg.Target,
    arm: cfg.Arm,
    rung: str,
    args: argparse.Namespace,
) -> res.ResultRow:
    started_wall = time.perf_counter()
    target_bytes = cfg.parse_size(rung)
    stamp = time.strftime("%Y%m%d%H%M%S")
    run_id = "%s_%s_%s_%s" % (target.name, arm.name, cfg.rung_label(rung), stamp)
    row = res.ResultRow(
        run_id=run_id,
        timestamp_utc=res.utc_now(),
        target=target.name,
        base_url=target.base_url,
        arm=arm.name,
        rung=rung,
        delimiter=arm.delimiter,
        source_file=str(arm.source),
        schema_fingerprint=res.schema_fingerprint(arm.columns, arm.constraints),
        target_bytes=target_bytes,
        notes=arm.note,
    )
    detail: dict = {"arm": arm.to_dict(), "rung": rung, "target": asdict(target)}

    log("\n=== rung %s (%s arm, target %s)" % (rung, arm.name, target.name))
    if not arm.source.exists():
        raise BenchError("reference file missing: %s" % arm.source)

    # 1. slice, CSV-aware
    sliced, slice_seconds, cached = make_slice(
        arm, target_bytes, Path(args.work_dir), not args.no_cache
    )
    row.slice_bytes = sliced.actual_bytes
    row.slice_rows = sliced.rows
    row.slice_rewritten = sliced.rewritten
    row.slice_passes = sliced.source_passes
    row.slice_seconds = round(slice_seconds, 3)
    log(
        "  slice: %d rows, %d bytes (%.1f%% of target)%s in %.1fs"
        % (
            sliced.rows,
            sliced.actual_bytes,
            100 * sliced.fill_ratio,
            " [cached]" if cached else "",
            slice_seconds,
        )
    )
    detail["slice"] = asdict(sliced)

    # 2. prove the slice is valid CSV rather than assume it
    expected_columns = len(arm.columns) if arm.columns else None
    if args.verify_slice and expected_columns:
        if sliced.actual_bytes <= args.verify_max_bytes:
            v_rows, counts = slicing.verify_slice(
                sliced.path, expected_columns, arm.csv_delimiter
            )
            if v_rows != sliced.rows or counts != {expected_columns}:
                raise BenchError(
                    "slice verification FAILED: re-parsed %d rows (expected %d), "
                    "field counts %s (expected {%d})"
                    % (v_rows, sliced.rows, sorted(counts), expected_columns)
                )
            row.slice_verified = "reparsed ok: %d rows x %d cols" % (
                v_rows,
                expected_columns,
            )
        else:
            row.slice_verified = "skipped (>%d bytes)" % args.verify_max_bytes
        log("  verify: %s" % row.slice_verified)

    # 3. transport: pre-compress so client CPU is not inside the transfer
    payload = sliced.path
    if args.gzip:
        gz = sliced.path.with_name(sliced.path.name + ".gz")
        if args.no_cache or not gz.exists():
            wire_bytes, compress_seconds = compress(sliced.path, gz, args.gzip_level)
        else:
            wire_bytes, compress_seconds = gz.stat().st_size, 0.0
        payload = gz
        row.gzip_level = str(args.gzip_level)
        row.wire_bytes = wire_bytes
        row.compress_seconds = round(compress_seconds, 3)
        log(
            "  gzip -%d: %d -> %d bytes (%.2f:1) in %.1fs"
            % (
                args.gzip_level,
                sliced.actual_bytes,
                wire_bytes,
                sliced.actual_bytes / max(wire_bytes, 1),
                compress_seconds,
            )
        )
    else:
        row.gzip_level = "none"
        row.wire_bytes = sliced.actual_bytes

    if args.dry_run:
        would_be = table_name(arm.name, rung, stamp)
        row.outcome = "dry-run"
        row.table = would_be
        row.notes = ("%s | table NOT created (dry run)" % arm.note).strip(" |")
        row.compute_derived()
        row.rung_wall_seconds = round(time.perf_counter() - started_wall, 3)
        log("  DRY RUN: nothing is sent.")
        log(
            "  would PUT %s/api/v0/tables/%s/?is_sandbox=1 with %s"
            % (
                target.base_url,
                would_be,
                json.dumps(
                    {"query": {"columns": arm.columns, "constraints": arm.constraints}}
                ),
            )
        )
        log(
            "  would POST %s (%d bytes, Content-Encoding: %s) to "
            "%s/api/v0/tables/%s/bulk-upload?delimiter=%s"
            % (
                payload.name,
                row.wire_bytes,
                "gzip" if args.gzip else "identity",
                target.base_url,
                would_be,
                arm.delimiter,
            )
        )
        log("  would then DELETE the table and confirm it is gone")
        return row

    # 4. fresh table for this rung
    guard_production(target, args.i_am_a_human_confirming_production, "create a table")
    name = table_name(arm.name, rung, stamp)
    row.table = name
    created = client.create_table(name, arm.columns, arm.constraints)
    detail["create"] = asdict(created)
    log("  create %s: %s" % (name, describe_http(created)[:200]))
    if not created.ok:
        row.outcome = "create-failed"
        row.http_status = str(created.status)
        row.responder = created.responder
        row.error = created.error or created.body[:500]
        row.response_body = created.body[:1000]
        row.rung_wall_seconds = round(time.perf_counter() - started_wall, 3)
        return row
    row.table_created = True

    # 5. upload, and always clean up afterwards
    try:
        log("  uploading %d bytes ..." % row.wire_bytes)
        upload = client.upload(
            name,
            payload,
            delimiter=arm.delimiter,
            gzipped=bool(args.gzip),
        )
        detail["upload"] = asdict(upload)
        row.connect_seconds = round(upload.connect_seconds, 3)
        row.send_seconds = round(upload.send_seconds, 3)
        row.wait_seconds = round(upload.wait_seconds, 3)
        row.read_seconds = round(upload.read_seconds, 3)
        row.upload_seconds = round(upload.total_seconds, 3)
        row.http_status = str(upload.status) if upload.status is not None else "none"
        row.responder = upload.responder
        row.server_header = upload.headers.get("Server", "")
        row.response_body = upload.body[:1500]
        row.error = upload.error
        row.wire_bytes_sent = upload.bytes_sent
        log("  upload: %s" % describe_http(upload))
        body = upload.json()
        if upload.ok and isinstance(body, dict):
            row.rows_reported = str(body.get("rows", ""))
            row.event_id = str(body.get("event_id", ""))
            id_range = body.get("id_range") or [None, None]
            row.id_min, row.id_max = str(id_range[0]), str(id_range[1])
            row.outcome = "success"
        else:
            row.outcome = _failure_label(upload)
            log("  !! %s" % row.outcome)

        if upload.ok and args.rowcount:
            counted = client.row_count(name)
            detail["rowcount"] = asdict(counted)
            data = counted.json()
            if isinstance(data, dict):
                try:
                    row.rowcount_after = str(data["data"][0][0])
                except (KeyError, IndexError, TypeError):
                    row.rowcount_after = counted.body[:80]
    finally:
        # cleanup is part of the run, never deferred (map standing rule)
        if row.table_created and not args.keep_table:
            dropped = client.drop_table(name)
            detail["drop"] = asdict(dropped)
            row.table_dropped = bool(dropped.ok)
            gone = client.describe_table(name)
            detail["confirm_gone"] = asdict(gone)
            row.drop_verified = (
                "gone (404)" if gone.status == 404 else "STILL THERE: %s" % gone.status
            )
            log(
                "  drop %s: %s / %s"
                % (name, describe_http(dropped)[:80], row.drop_verified)
            )
        elif args.keep_table:
            row.drop_verified = "KEPT (--keep-table): drop it by hand"
            log("  !! table %s kept on purpose - drop it by hand" % name)

    row.compute_derived()
    row.rung_wall_seconds = round(time.perf_counter() - started_wall, 3)
    detail["row"] = asdict(row)
    row.detail_file = str(
        res.write_detail(Path(args.results).parent / "detail", run_id, detail)
    )
    return row


def _failure_label(upload: HttpResult) -> str:
    """Name the failure by WHO answered, never by the status alone."""
    if upload.status is None:
        return "transport-failure"
    who = {PLATFORM: "platform", PROXY: "proxy/front-end"}.get(
        upload.responder, "unidentified responder"
    )
    return "HTTP %s from %s" % (upload.status, who)


# --- main ----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m benchmarks.bulk_upload.run",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        default="toep",
        help="named target (%s) or a base URL" % ", ".join(cfg.TARGETS),
    )
    parser.add_argument(
        "--arm", default="narrow", help="arm name (%s)" % ", ".join(cfg.ARMS)
    )
    parser.add_argument(
        "--arms-file",
        help="JSON file of arm definitions; how a schema decision plugs in",
    )
    parser.add_argument(
        "--rungs",
        default="1MB",
        help="comma separated sizes, e.g. 1MB,10MB,100MB,1GB,1.95GB",
    )
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument(
        "--work-dir",
        default=str(Path(tempfile.gettempdir()) / "oep_bulk_bench"),
        help="where slices and their .gz live (they are large)",
    )
    parser.add_argument("--no-cache", action="store_true", help="re-slice every time")
    parser.add_argument("--gzip", action="store_true", default=True)
    parser.add_argument(
        "--no-gzip", dest="gzip", action="store_false", help="send the CSV uncompressed"
    )
    parser.add_argument("--gzip-level", type=int, default=6)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--insecure", action="store_true", help="skip TLS verification")
    parser.add_argument(
        "--dry-run", action="store_true", help="everything but the send"
    )
    parser.add_argument("--check-auth", action="store_true")
    parser.add_argument("--probe-body-limit", action="store_true")
    parser.add_argument("--keep-table", action="store_true")
    parser.add_argument("--rowcount", action="store_true", default=True)
    parser.add_argument("--no-rowcount", dest="rowcount", action="store_false")
    parser.add_argument("--verify-slice", action="store_true", default=True)
    parser.add_argument("--no-verify-slice", dest="verify_slice", action="store_false")
    parser.add_argument(
        "--verify-max-bytes",
        type=int,
        default=2 * 10**9,
        help=(
            "above this, skip re-parsing the slice (measured: re-parsing the "
            "full 1.95 GB fat slice costs ~12 s, so the default covers every "
            "rung on this map's staircase)"
        ),
    )
    parser.add_argument(
        "--i-am-a-human-confirming-production",
        action="store_true",
        help="required for any write against a production target",
    )
    return parser


def resolve_target(name: str) -> cfg.Target:
    if name in cfg.TARGETS:
        return cfg.TARGETS[name]
    if "://" in name:
        parts = urlsplit(name)
        # the short name ends up in run ids and file names, so it must not
        # carry a scheme or a colon
        short = re.sub(r"[^a-z0-9]+", "_", (parts.netloc or name).lower()).strip("_")
        return cfg.Target(name=short or "custom", base_url=name, is_production=False)
    raise BenchError(
        "unknown target %r: use one of %s or a full base URL"
        % (name, ", ".join(cfg.TARGETS))
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        target = resolve_target(args.target)
        if args.insecure and target.is_production:
            raise BenchError(
                "--insecure against production is refused: it would send the "
                "account's token over a connection nobody authenticated. "
                "Production's certificate chain is valid; if it stopped "
                "verifying, that is an incident, not a flag to pass."
            )
        # the probe is unauthenticated and a dry run never sends anything,
        # so only a real run (or --check-auth) needs the credential
        probe_only = args.probe_body_limit and not args.check_auth
        token = read_token(required=not (probe_only or args.dry_run))
        client = BenchClient(
            target.base_url,
            token=token,
            timeout=args.timeout,
            insecure=args.insecure,
        )
        if args.insecure:
            log(
                "!! --insecure: TLS certificates are NOT verified. The token "
                "will be sent to whoever answers %s. Only acceptable because "
                "toep.iks.cs.ovgu.de serves an incomplete certificate chain; "
                "never use it against production." % target.base_url
            )

        if args.probe_body_limit and not args.check_auth:
            probe_body_limit(client)
            return 0

        if args.check_auth:
            report = check_auth(client, target, args.i_am_a_human_confirming_production)
            out = Path(args.results).parent / "detail"
            path = res.write_detail(
                out, "checkauth_%s_%s" % (target.name, uuid.uuid4().hex[:8]), report
            )
            log("\nfull preflight record: %s" % path)
            return 0

        arms = cfg.load_arms(Path(args.arms_file)) if args.arms_file else cfg.ARMS
        if args.arm not in arms:
            raise BenchError(
                "unknown arm %r: known arms are %s" % (args.arm, ", ".join(arms))
            )
        arm = arms[args.arm]
        rungs = [r.strip() for r in args.rungs.split(",") if r.strip()]

        log("target      : %s (%s)" % (target.name, target.base_url))
        log("arm         : %s <- %s" % (arm.name, arm.source))
        log("schema hash : %s" % res.schema_fingerprint(arm.columns, arm.constraints))
        log("rungs       : %s" % ", ".join(rungs))
        log("results     : %s" % args.results)
        if arm.note:
            log("arm note    : %s" % arm.note)

        exit_code = 0
        for rung in rungs:
            row = run_rung(client, target, arm, rung, args)
            res.append_row(Path(args.results), row)
            log("  recorded: %s %s" % (row.outcome, row.detail_file))
            if row.outcome not in ("success", "dry-run"):
                log(
                    "\nSTOPPING the staircase at %s: %s. That failure IS the "
                    "finding - read the response body above and say which "
                    "layer answered before climbing further." % (rung, row.outcome)
                )
                exit_code = 2
                break
        return exit_code
    except BenchError as exc:
        log("\nERROR: %s" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
