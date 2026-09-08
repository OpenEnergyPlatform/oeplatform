"""Benchmark harness for the Bulk Upload path (issue #2362).

Measures the LIVE endpoint - `POST /api/v0/tables/<table>/bulk-upload` -
end to end from a client, one "rung" (one target payload size) at a time:
slice a rung-sized CSV out of a reference file, create a fresh sandbox
table, upload it gzipped, time the phases, append a result row, drop the
table.

See `run.py` for the command line. Nothing here imports Django.
"""
