"""CSV-aware slicing of a reference file into rung-sized benchmark inputs.

Why this module exists at all: the fat reference file
(`open_modex_bsf_timeseries.csv`) carries a ~111 KB quoted JSON array per
row, and that array is full of commas. Cutting it with `head -c` splits a
record, COPY fails on the truncated line, and the run measures a rollback
instead of a load. So slices are cut on RECORD boundaries, found with a
quote-aware scanner, and the target byte size is a target: the actual
bytes and the actual row count are measured, never assumed.

The scanner works on bytes and hands back the original record bytes, so
the default path copies records verbatim - no decode/re-encode, no change
in what is being measured. Only the optional projection path (dropping or
renumbering columns) rewrites records, and it says so in its result.
"""

from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

READ_CHUNK = 1 << 20  # 1 MiB

# CSV fields can legally be far larger than the stdlib default 128 KiB
# limit - the fat file's `series` column is already ~111 KB.
csv.field_size_limit(64 * 1024 * 1024)

_QUOTE = 0x22


class SliceError(RuntimeError):
    """Raised when a slice cannot be produced as configured."""


def iter_records(fh, chunk_size: int = READ_CHUNK) -> Iterator[tuple[int, int, bytes]]:
    """Yield `(start, end, data)` for each RFC 4180 record in `fh`.

    A record ends at the first newline that is NOT inside a quoted field;
    doubled quotes (`""`) inside a quoted field are handled. `data` is the
    record exactly as written, terminating newline (and the CR of a CRLF
    pair) included, so writing it out reproduces the source byte for byte.
    The header is simply the first record.

    `fh` must be binary and positioned at the start, and must not be
    touched by the caller while iterating: this generator owns the file
    position. Memory stays bounded by one record plus one chunk.
    """
    buf = b""
    base = 0  # absolute offset of buf[0]
    i = 0  # scan cursor inside buf
    record_start = 0  # absolute offset of the record being scanned
    in_quotes = False
    eof = False

    def refill() -> bool:
        """Drop bytes before the current record, then read one chunk."""
        nonlocal buf, base, i
        keep = record_start - base
        if keep:
            buf = buf[keep:]
            base += keep
            i -= keep
        more = fh.read(chunk_size)
        if not more:
            return False
        buf += more
        return True

    while True:
        if in_quotes:
            j = buf.find(b'"', i)
            if j == -1:
                i = len(buf)
                if eof:
                    break
                eof = not refill()
                continue
            if j + 1 >= len(buf):
                # cannot yet tell a closing quote from an escaped one
                if not eof:
                    eof = not refill()
                    continue
                in_quotes = False
                i = j + 1
                continue
            if buf[j + 1] == _QUOTE:
                i = j + 2  # escaped quote, still inside the field
            else:
                in_quotes = False
                i = j + 1
            continue

        q = buf.find(b'"', i)
        n = buf.find(b"\n", i)
        if q == -1 and n == -1:
            i = len(buf)
            if eof:
                break
            eof = not refill()
            continue
        if n == -1 or (q != -1 and q < n):
            in_quotes = True
            i = q + 1
            continue
        end = base + n + 1
        yield record_start, end, buf[record_start - base : end - base]
        record_start = end
        i = n + 1

    tail_end = base + len(buf)
    if tail_end > record_start:
        # a final record without a trailing newline
        yield record_start, tail_end, buf[record_start - base :]


@dataclass
class SliceResult:
    """What a slice actually is - measured, not intended."""

    path: Path
    target_bytes: int
    actual_bytes: int  # including the header line
    rows: int  # data rows, header excluded
    header_bytes: int
    source_records_read: int
    source_passes: int  # >1 means the source was repeated to fill the rung
    rewritten: bool  # True if records were re-serialised (projection path)

    @property
    def fill_ratio(self) -> float:
        return self.actual_bytes / self.target_bytes if self.target_bytes else 0.0


def read_header(path: Path) -> bytes:
    """The first record of a CSV file, newline included."""
    with open(path, "rb") as fh:
        for _start, _end, data in iter_records(fh):
            return data
    raise SliceError("reference file %s has no header record" % path)


def header_columns(path: Path, delimiter: str = ",") -> list[str]:
    """Column names of a reference file, in file order."""
    text = read_header(path).decode("utf-8").rstrip("\r\n")
    return next(csv.reader(io.StringIO(text), delimiter=delimiter))


def _project(
    record: bytes,
    keep_index: list[int],
    delimiter: str,
    id_position: int | None,
    next_id: int | None,
) -> bytes:
    text = record.decode("utf-8").rstrip("\r\n")
    fields = next(csv.reader(io.StringIO(text), delimiter=delimiter))
    kept = [fields[k] for k in keep_index]
    if id_position is not None and next_id is not None:
        kept[id_position] = str(next_id)
    out = io.StringIO()
    csv.writer(out, delimiter=delimiter, lineterminator="\n").writerow(kept)
    return out.getvalue().encode("utf-8")


def slice_csv(
    source: Path,
    dest: Path,
    target_bytes: int,
    *,
    delimiter: str = ",",
    drop_columns: Iterable[str] = (),
    renumber_id: bool = False,
    repeat: bool = False,
    max_passes: int = 200,
) -> SliceResult:
    """Write a rung-sized, valid CSV slice of `source` to `dest`.

    Records are added whole until the next one would exceed
    `target_bytes`; at least one record is always written. The header is
    always present. Nothing is held in memory beyond one record.

    `drop_columns` and `renumber_id` switch on the projection path, which
    re-serialises every record (slower, and the bytes are no longer the
    source's bytes - `SliceResult.rewritten` records that). `repeat`
    cycles the source when it is smaller than the rung; that would
    duplicate `id` values, which the bulk upload id contract rejects, so
    `id` must then be dropped or renumbered.
    """
    source = Path(source)
    dest = Path(dest)
    drop = list(drop_columns)
    columns = header_columns(source, delimiter=delimiter)
    for name in drop:
        if name not in columns:
            raise SliceError(
                "cannot drop column %r: not in %s header %s" % (name, source, columns)
            )
    keep = [c for c in columns if c not in drop]
    if not keep:
        raise SliceError("dropping %s would leave no columns" % drop)
    keep_index = [columns.index(c) for c in keep]

    id_position = keep.index("id") if "id" in keep else None
    if renumber_id and id_position is None:
        raise SliceError("renumber_id requested but no 'id' column is emitted")
    if repeat and id_position is not None and not renumber_id:
        raise SliceError(
            "repeating the source would duplicate 'id' values, which the bulk "
            "upload id contract rejects: drop 'id' or set renumber_id"
        )

    rewritten = bool(drop) or renumber_id
    if rewritten:
        out = io.StringIO()
        csv.writer(out, delimiter=delimiter, lineterminator="\n").writerow(keep)
        header_bytes = out.getvalue().encode("utf-8")
    else:
        header_bytes = read_header(source)
        if not header_bytes.endswith(b"\n"):
            header_bytes += b"\n"

    dest.parent.mkdir(parents=True, exist_ok=True)
    total = len(header_bytes)
    rows = 0
    records_read = 0
    passes = 0
    next_id = 1
    tmp = dest.with_name(dest.name + ".partial")

    with open(tmp, "wb") as out_fh:
        out_fh.write(header_bytes)
        done = False
        while not done:
            passes += 1
            if passes > max_passes:
                raise SliceError(
                    "source %s exhausted after %d passes without reaching %d bytes"
                    % (source, max_passes, target_bytes)
                )
            wrote_this_pass = False
            with open(source, "rb") as in_fh:
                for index, (_start, _end, record) in enumerate(iter_records(in_fh)):
                    if index == 0:
                        continue  # the source header, already handled
                    records_read += 1
                    if rewritten:
                        record = _project(
                            record,
                            keep_index,
                            delimiter,
                            id_position,
                            next_id if renumber_id else None,
                        )
                    elif not record.endswith(b"\n"):
                        record += b"\n"
                    if rows and total + len(record) > target_bytes:
                        done = True
                        break
                    out_fh.write(record)
                    total += len(record)
                    rows += 1
                    next_id += 1
                    wrote_this_pass = True
                    if total >= target_bytes:
                        done = True
                        break
            if not done and not repeat:
                done = True
            if not done and not wrote_this_pass:
                raise SliceError("source %s yielded no data records" % source)

    os.replace(tmp, dest)
    actual = dest.stat().st_size
    if actual != total:
        raise SliceError(
            "slice bookkeeping mismatch: counted %d bytes, file is %d" % (total, actual)
        )
    return SliceResult(
        path=dest,
        target_bytes=target_bytes,
        actual_bytes=actual,
        rows=rows,
        header_bytes=len(header_bytes),
        source_records_read=records_read,
        source_passes=passes,
        rewritten=rewritten,
    )


def verify_slice(
    path: Path, expected_columns: int, delimiter: str = ","
) -> tuple[int, set[int]]:
    """Re-parse a slice with the stdlib CSV reader.

    Returns `(data_rows, {field counts seen})`. If the slicer ever cut a
    record in half this is where it shows: a parse error, or a row whose
    field count differs from the header's.
    """
    counts: set[int] = set()
    rows = 0
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        header = next(reader)
        counts.add(len(header))
        if len(header) != expected_columns:
            raise SliceError(
                "header has %d columns, expected %d" % (len(header), expected_columns)
            )
        for row in reader:
            rows += 1
            counts.add(len(row))
    return rows, counts
