"""Targets, arms and rungs - everything a run is described by.

Column definitions are DATA here, not code, and can be replaced wholesale
from a JSON file (`--arms-file`). They are a deliberate input to the
measurement: typing the fat file's `series` column as `text` measures raw
ingest, typing it as `json`/`jsonb` measures validated-JSON ingest, and
those are different benchmarks. The values below are PROVISIONAL until
the schema decision lands; whoever changes them must re-run every rung
that is meant to be comparable.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# --- targets -------------------------------------------------------------

DEFAULT_REFERENCE_DIR = Path(
    "/home/jh/github/oep-upload/data/datapackages/example/data"
)


@dataclass(frozen=True)
class Target:
    """One deployment the harness can be pointed at."""

    name: str
    base_url: str
    is_production: bool = False


TARGETS: dict[str, Target] = {
    "prod": Target(
        name="prod",
        base_url="https://openenergyplatform.org",
        is_production=True,
    ),
    # NOTE (measured 2026-08-07): toep serves an INCOMPLETE TLS chain - the
    # leaf only, without its Let's Encrypt intermediate - so curl, requests
    # and this harness all fail with "unable to get local issuer
    # certificate". Until the host serves the full chain, runs against toep
    # need --insecure. Its `Server` header is otherwise byte-identical to
    # production's (Apache/2.4.52 Ubuntu, OpenSSL 3.0.2, mod_wsgi 4.9.0,
    # Python 3.10), which is what makes it a fair rehearsal surface.
    "toep": Target(name="toep", base_url="https://toep.iks.cs.ovgu.de"),
    "local": Target(name="local", base_url="http://127.0.0.1:8000"),
}


# --- arms ----------------------------------------------------------------


@dataclass
class Arm:
    """One shape of data: which file, which columns, which table."""

    name: str
    source: Path
    delimiter: str = "comma"  # the API's delimiter parameter name
    #: table-create payload, sent as {"query": {"columns": [...],
    #: "constraints": [...]}} to PUT /api/v0/tables/<name>/
    columns: list[dict] = field(default_factory=list)
    constraints: list[dict] = field(default_factory=list)
    #: columns removed from every sliced record before upload
    drop_columns: tuple[str, ...] = ()
    #: rewrite `id` with a fresh counter (required when repeating a source)
    renumber_id: bool = False
    #: cycle the source file when a rung is larger than it
    repeat: bool = False
    note: str = ""

    @property
    def csv_delimiter(self) -> str:
        return {"comma": ",", "semicolon": ";", "tab": "\t"}[self.delimiter]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source": str(self.source),
            "delimiter": self.delimiter,
            "columns": self.columns,
            "constraints": self.constraints,
            "drop_columns": list(self.drop_columns),
            "renumber_id": self.renumber_id,
            "repeat": self.repeat,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Arm":
        return cls(
            name=data["name"],
            source=Path(data["source"]),
            delimiter=data.get("delimiter", "comma"),
            columns=data.get("columns", []),
            constraints=data.get("constraints", []),
            drop_columns=tuple(data.get("drop_columns", ())),
            renumber_id=bool(data.get("renumber_id", False)),
            repeat=bool(data.get("repeat", False)),
            note=data.get("note", ""),
        )


# NOTE ON `id` AND THE PRIMARY KEY (verified against api/parser.py):
# the table-create endpoint ALWAYS ends up with a primary key on `id` - if
# no `id` column is given it invents one (BigInteger, autoincrement), and
# if no primary key is given it adds PRIMARY KEY (id); a primary key on
# anything other than `id` is rejected outright. So "no index during COPY"
# is not an option the API offers, and every rung pays the pk index cost.
# The only real choice is whether the CSV SUPPLIES ids (exercising the
# slice-4 id contract) or omits them (letting the sequence generate them).

ARMS: dict[str, Arm] = {
    "fat": Arm(
        name="fat",
        source=DEFAULT_REFERENCE_DIR / "open_modex_bsf_timeseries.csv",
        columns=[
            {"name": "id", "data_type": "bigint"},
            {"name": "timeindex_start", "data_type": "text"},
            {"name": "timeindex_stop", "data_type": "text"},
            {"name": "timeindex_resolution", "data_type": "text"},
            {"name": "series", "data_type": "text"},
        ],
        note=(
            "PROVISIONAL pending the schema decision: `series` as text "
            "measures raw ingest, not validated-JSON ingest"
        ),
    ),
    "narrow": Arm(
        name="narrow",
        source=DEFAULT_REFERENCE_DIR / "open_modex_bsf_data.csv",
        columns=[
            {"name": "id", "data_type": "bigint"},
            {"name": "scenario_id", "data_type": "bigint"},
            {"name": "region", "data_type": "text"},
            {"name": "input_energy_vector", "data_type": "text"},
            {"name": "output_energy_vector", "data_type": "text"},
            {"name": "parameter_name", "data_type": "text"},
            {"name": "technology", "data_type": "text"},
            {"name": "technology_type", "data_type": "text"},
            {"name": "type", "data_type": "text"},
            {"name": "unit", "data_type": "text"},
            {"name": "tags", "data_type": "text"},
            {"name": "method", "data_type": "text"},
            {"name": "source", "data_type": "text"},
            {"name": "comment", "data_type": "text"},
        ],
        note="PROVISIONAL pending the schema decision",
    ),
}


def load_arms(path: Path) -> dict[str, Arm]:
    """Replace/extend the built-in arms from a JSON file.

    The file is a list of arm dicts (see `Arm.to_dict`), which is how the
    schema decision plugs in without touching this module.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    arms = dict(ARMS)
    for entry in data:
        arm = Arm.from_dict(entry)
        arms[arm.name] = arm
    return arms


# --- rungs ---------------------------------------------------------------

_UNITS = {
    "": 1,
    "b": 1,
    "kb": 10**3,
    "mb": 10**6,
    "gb": 10**9,
    "kib": 1024,
    "mib": 1024**2,
    "gib": 1024**3,
}

_SIZE_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([a-zA-Z]*)\s*$")

#: the staircase fixed when this map was charted
DEFAULT_RUNGS = ["1MB", "10MB", "100MB", "1GB", "1.95GB"]


def parse_size(text: str) -> int:
    """`"1.95GB"` -> bytes. Decimal MB/GB, binary MiB/GiB, both explicit."""
    match = _SIZE_RE.match(text)
    if not match:
        raise ValueError("cannot parse size %r" % text)
    number, unit = match.groups()
    key = unit.lower()
    if key not in _UNITS:
        raise ValueError(
            "unknown size unit %r in %r (use %s)"
            % (unit, text, ", ".join(sorted(u for u in _UNITS if u)))
        )
    return int(float(number) * _UNITS[key])


def rung_label(text: str) -> str:
    """A table-name-safe label for a rung, e.g. `1.95GB` -> `1_95gb`."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
