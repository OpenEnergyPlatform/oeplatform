"""What "realistic" means for a seeded factsheet corpus.

Everything here is CALIBRATION, not code to be improved: each number was
measured against production on 2026-09-01 by a cheap, read-only probe, and
whoever changes one must say which probe replaced it. The point of the file
is that a local, synthetic corpus reproduces production's COST STRUCTURE -
not its content.

Two calibrations matter, because they drive the two cost sites the map found:

* `field_profile.json` - per-column mean character and word count over all
  305 production models, taken from `/factsheets/models/download/`
  (794,853 bytes, 305 x 192, one 0.31 s request). Word count is the one that
  decides payload: the row builder (`modelview.list_payload`, and before it
  the template filter it replaced) truncates every string to 12 words, so a
  4,532-character field renders as twelve words. Character count only decides
  what Postgres stores.

* `TAG_DISTRIBUTION` - the factsheet->tag edge count per factsheet, from a
  30-sheet sample of detail pages (every ~10th id, 21 s of cheap requests).
  This is the number the payload used to multiply by seven -- once per
  view-property group, each an uncached `model.tags.all` -- so a corpus that
  gets it wrong measures the wrong page.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

PROFILE_PATH = Path(__file__).with_name("field_profile.json")

# Measured 2026-09-01: 30 factsheets sampled at every ~10th id, tag anchors
# counted on the detail page. Sorted counts were
#   0 x11, 1 x2, 2 x4, 3 x2, 4 x3, 5, 6, 7, 9 x2, 30, 696, 817
# -> 1,607 edges over 30 sheets = 53.6 mean, but the mean is meaningless:
# two corrupted sheets carry 94% of the edges. Model it as the mixture it is.
TAG_SAMPLE = [0] * 11 + [1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 4, 5, 6, 7, 9, 9, 30, 696, 817]

#: Fraction of factsheets carrying a "whole tag table" snapshot (the #2385
#: corruption). 2 of 30 sampled. Extrapolates to ~20 of 305 on production.
CORRUPT_FRACTION = 2 / 30

#: Tag counts seen on corrupted sheets - each is a snapshot of the tag table
#: at save time, which is why they differ (696 / 812 / 817 all observed).
CORRUPT_SNAPSHOT_SIZES = (696, 812, 817)

#: Tag counts on healthy sheets, sampled with replacement.
HEALTHY_TAG_COUNTS = [0] * 11 + [1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 4, 5, 6, 7, 9, 9, 30]

#: Production totals the default sweep rung is calibrated to.
PROD_MODELS = 305
PROD_TAGS = 817


@dataclass
class Corpus:
    """One seeded corpus: how many rows, of what shape."""

    models: int = PROD_MODELS
    tags: int = PROD_TAGS
    #: None -> use CORRUPT_FRACTION. 0.0 -> a corpus with no #2385 damage,
    #: which is what the platform looks like AFTER WF-03's repair; measuring
    #: both is how we tell "the page is slow" from "the data is broken".
    corrupt_fraction: float | None = None
    seed: int = 20260901

    def tag_counts(self) -> list[int]:
        """One tag count per factsheet, drawn from the measured mixture."""
        rng = random.Random(self.seed)
        frac = (
            CORRUPT_FRACTION if self.corrupt_fraction is None else self.corrupt_fraction
        )
        counts = []
        for _ in range(self.models):
            if rng.random() < frac:
                counts.append(min(self.tags, rng.choice(CORRUPT_SNAPSHOT_SIZES)))
            else:
                counts.append(min(self.tags, rng.choice(HEALTHY_TAG_COUNTS)))
        return counts

    def label(self) -> str:
        frac = (
            CORRUPT_FRACTION if self.corrupt_fraction is None else self.corrupt_fraction
        )
        return "m%d_t%d_c%.3f" % (self.models, self.tags, frac)


@dataclass
class FieldProfile:
    """Per-column mean chars/words, as measured on production."""

    columns: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path = PROFILE_PATH) -> "FieldProfile":
        return cls(columns=json.loads(path.read_text(encoding="utf-8")))

    def text_for(self, name: str, rng: random.Random) -> str:
        """A string with this column's measured word count and word length."""
        spec = self.columns.get(name)
        if not spec or rng.random() > spec["fill"]:
            return ""
        words = max(1, int(round(spec["words"])))
        per_word = max(1, int(round(spec["chars"] / max(1, spec["words"]))) - 1)
        return " ".join(
            "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(per_word))
            for _ in range(words)
        )
