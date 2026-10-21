"""Tests for the CSV-aware slicer.

The slicer is the piece that can silently poison every measurement: a
byte-sliced fat file fails mid-record, COPY rolls back, and the harness
reports the wall clock of a rollback as if it were a load. So the record
scanner is tested against handcrafted edge cases AND, when the reference
data is present on the machine, against the real files.
"""

from __future__ import annotations

import csv
import io
import unittest
from pathlib import Path

from benchmarks.bulk_upload import config
from benchmarks.bulk_upload.slicing import (
    SliceError,
    header_columns,
    iter_records,
    slice_csv,
    verify_slice,
)

FAT = config.DEFAULT_REFERENCE_DIR / "open_modex_bsf_timeseries.csv"
NARROW = config.DEFAULT_REFERENCE_DIR / "open_modex_bsf_data.csv"


def records(data: bytes, chunk_size: int = 8) -> list[bytes]:
    return [rec for _s, _e, rec in iter_records(io.BytesIO(data), chunk_size)]


class RecordScannerTests(unittest.TestCase):
    def test_plain_records(self):
        data = b"a,b\n1,2\n3,4\n"
        self.assertEqual(records(data), [b"a,b\n", b"1,2\n", b"3,4\n"])

    def test_quoted_comma_does_not_split(self):
        data = b'a,b\n1,"x,y,z"\n2,"p,q"\n'
        self.assertEqual(records(data), [b"a,b\n", b'1,"x,y,z"\n', b'2,"p,q"\n'])

    def test_quoted_newline_does_not_end_the_record(self):
        data = b'a,b\n1,"line one\nline two"\n2,"z"\n'
        self.assertEqual(
            records(data), [b"a,b\n", b'1,"line one\nline two"\n', b'2,"z"\n']
        )

    def test_escaped_quotes(self):
        data = b'a\n"he said ""hi"", then left"\n"next"\n'
        self.assertEqual(
            records(data),
            [b"a\n", b'"he said ""hi"", then left"\n', b'"next"\n'],
        )

    def test_crlf_is_preserved(self):
        data = b"a,b\r\n1,2\r\n"
        self.assertEqual(records(data), [b"a,b\r\n", b"1,2\r\n"])

    def test_missing_final_newline(self):
        data = b"a,b\n1,2"
        self.assertEqual(records(data), [b"a,b\n", b"1,2"])

    def test_chunk_boundaries_do_not_change_the_answer(self):
        data = b'a,b\n1,"x,""y"",\nz"\n2,"q"\n3,4\n'
        expected = records(data, chunk_size=4096)
        for size in (1, 2, 3, 5, 7, 13, 64):
            self.assertEqual(records(data, size), expected, "chunk size %d" % size)

    def test_bytes_are_conserved(self):
        data = b'a,b\n1,"x,y"\n2,"a""b"\n3,4\n'
        self.assertEqual(b"".join(records(data, 3)), data)

    def test_agrees_with_stdlib_csv_on_record_count(self):
        data = b'a,b\n1,"x,y"\n2,"line\nbreak"\n3,"q""q"\n'
        mine = len(records(data, 5))
        theirs = sum(1 for _ in csv.reader(io.StringIO(data.decode())))
        self.assertEqual(mine, theirs)


class SliceTests(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.source = self.dir / "source.csv"
        rows = "".join('%d,"a,b %d"\n' % (i, i) for i in range(1, 101))
        self.source.write_bytes(b"id,payload\n" + rows.encode())

    def test_header_is_always_carried(self):
        result = slice_csv(self.source, self.dir / "out.csv", 40)
        text = (self.dir / "out.csv").read_text()
        self.assertTrue(text.startswith("id,payload\n"))
        self.assertGreaterEqual(result.rows, 1)

    def test_never_exceeds_the_target_beyond_one_record(self):
        result = slice_csv(self.source, self.dir / "out.csv", 200)
        self.assertLessEqual(result.actual_bytes, 200)
        self.assertEqual(result.actual_bytes, (self.dir / "out.csv").stat().st_size)

    def test_at_least_one_row_even_for_a_tiny_target(self):
        result = slice_csv(self.source, self.dir / "out.csv", 1)
        self.assertEqual(result.rows, 1)

    def test_target_larger_than_source_stops_at_the_source(self):
        result = slice_csv(self.source, self.dir / "out.csv", 10**9)
        self.assertEqual(result.rows, 100)
        self.assertEqual(result.source_passes, 1)

    def test_repeat_requires_id_handling(self):
        with self.assertRaises(SliceError):
            slice_csv(self.source, self.dir / "out.csv", 10**5, repeat=True)

    def test_repeat_with_renumbered_ids_is_monotonic(self):
        result = slice_csv(
            self.source,
            self.dir / "out.csv",
            20_000,
            repeat=True,
            renumber_id=True,
        )
        self.assertGreater(result.source_passes, 1)
        self.assertTrue(result.rewritten)
        with open(self.dir / "out.csv", newline="") as fh:
            reader = csv.reader(fh)
            next(reader)
            ids = [int(r[0]) for r in reader]
        self.assertEqual(ids, list(range(1, len(ids) + 1)))

    def test_dropping_a_column(self):
        result = slice_csv(
            self.source, self.dir / "out.csv", 10**6, drop_columns=("id",)
        )
        rows, counts = verify_slice(self.dir / "out.csv", 1)
        self.assertEqual(rows, result.rows)
        self.assertEqual(counts, {1})

    def test_dropping_an_unknown_column_is_an_error(self):
        with self.assertRaises(SliceError):
            slice_csv(self.source, self.dir / "out.csv", 100, drop_columns=("nope",))


@unittest.skipUnless(
    FAT.exists() and NARROW.exists(),
    "reference data not present on this machine (%s)" % config.DEFAULT_REFERENCE_DIR,
)
class ReferenceFileTests(unittest.TestCase):
    """The claim that matters: real slices of the real files parse."""

    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_fat_slice_is_valid_csv_with_five_columns(self):
        columns = header_columns(FAT)
        self.assertEqual(len(columns), 5)
        out = self.dir / "fat.csv"
        result = slice_csv(FAT, out, 10 * 10**6)
        rows, counts = verify_slice(out, 5)
        self.assertEqual(rows, result.rows)
        self.assertEqual(counts, {5}, "a split record would show up as a short row")
        self.assertLessEqual(result.actual_bytes, 10 * 10**6)
        # the fat file's records are ~111 KB, so a 10 MB rung is ~90 rows
        self.assertGreater(result.rows, 10)

    def test_fat_slice_bytes_are_the_source_bytes(self):
        out = self.dir / "fat.csv"
        result = slice_csv(FAT, out, 2 * 10**6)
        self.assertFalse(result.rewritten)
        with open(FAT, "rb") as fh:
            prefix = fh.read(result.actual_bytes)
        self.assertEqual(
            out.read_bytes(),
            prefix,
            "an unrewritten slice must be a byte-exact prefix of the source",
        )

    def test_narrow_slice_is_valid_csv_with_fourteen_columns(self):
        out = self.dir / "narrow.csv"
        result = slice_csv(NARROW, out, 5 * 10**6)
        rows, counts = verify_slice(out, 14)
        self.assertEqual(rows, result.rows)
        self.assertEqual(counts, {14})

    def test_narrow_full_scan_matches_the_stdlib_reader(self):
        with open(NARROW, "rb") as fh:
            mine = sum(1 for _ in iter_records(fh))
        with open(NARROW, newline="", encoding="utf-8") as fh:
            theirs = sum(1 for _ in csv.reader(fh))
        self.assertEqual(mine, theirs)


if __name__ == "__main__":
    unittest.main()
