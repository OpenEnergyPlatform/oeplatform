"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The Publish gate: the checks a Table's metadata must pass before publishing
it would succeed, declared once (spec #2551); and beside it the Dataset's
own gate, ``DATASET_GATE`` (spec #2613).

Three readers run exactly ``PUBLISH_GATE``, so they cannot disagree about
what the gate is:

- the stored flag ``Table.publishable``, recomputed by
  ``api.actions.set_table_metadata``, the one metadata write path;
- the management command ``recompute_publish_gate``, which evaluates every
  Table, run on the deploy that adds the field and on any deploy that changes
  this list;
- the Publishable column of the profile dashboard's tables tab, which runs
  the checks live for the rows on screen to give the reasons.

Publishing itself (``api.actions.move_publish``) validates live and never
reads the stored flag, so a stale flag can mislabel a row but never publish
one.
"""  # noqa: 501

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class GateCheck:
    """One check of the Publish gate: ``name`` is what a failing row shows,
    ``label`` what the reasons popover calls it, ``run`` the check itself,
    answering ``{"status": bool, "error": str}`` like
    ``Table.validate_open_data_license``. A check must not raise."""

    name: str
    label: str
    run: Callable


@dataclass(frozen=True)
class CheckResult:
    """What one Publish gate check said about one Table."""

    name: str
    label: str
    passed: bool
    reason: str = ""


# The checks the Publish gate enforces, in the order a row names them. Today
# that is the open data license alone, the one content refusal publishing
# makes (``api.actions.move_publish`` refuses a publish on exactly this
# check), so ✓ means "publishing will not refuse this Table on its content".
#
# A check joins the column, the gate and the recompute in the same change.
# The column and the stored flag follow this list by themselves; what the
# change must do by hand is make publishing refuse on the new check, and add
# "run recompute_publish_gate --apply" to that release's deploy checklist,
# because every stored flag was computed without the new check.
PUBLISH_GATE = (
    GateCheck("License", "Open data license", lambda t: t.validate_open_data_license()),
)


def publish_checks(subject, gate=PUBLISH_GATE) -> list:
    """Every check of ``gate`` (the Table's Publish gate unless another is
    named), run on ``subject`` now."""
    results = []
    for check in gate:
        outcome = check.run(subject)
        passed = bool(outcome["status"])
        results.append(
            CheckResult(
                check.name, check.label, passed, "" if passed else outcome["error"]
            )
        )
    return results


def passes(checks) -> bool:
    """Whether a Table whose checks came out as ``checks`` passes the gate."""
    return all(check.passed for check in checks)


def is_publishable(table) -> bool:
    """The gate's verdict on ``table`` now: what ``Table.publishable``
    stores."""
    return passes(publish_checks(table))


def _verdict(passed, error) -> dict:
    return {"status": passed, "error": "" if passed else error}


# The Dataset's Publish gate (spec #2613, WF-03): what publishing a Dataset
# needs, run live at the moment of publishing by the Dataset action service
# (``api.services.dataset_actions``) and never stored -- a user has a handful
# of Datasets, and the gate is two EXISTS.
#
# **The names are a contract**: the API's 409 lists the failed checks by
# ``name`` (``{"failed": ["members", "topics"]}``), so a pipeline can react
# without parsing prose. Renaming one is a breaking change of the API.
#
# Title and description need no check (every write requires them), and a
# license is a member Table's, not the Dataset's. Nothing about a member's
# own state counts: a published Dataset may hold draft and embargoed Tables.
# The gate judges the transition only, so a published Dataset that stops
# passing stays published.
DATASET_GATE = (
    GateCheck(
        "members",
        "Member tables",
        lambda dataset: _verdict(dataset.tables.exists(), "No member tables"),
    ),
    GateCheck(
        "topics",
        "Topics",
        lambda dataset: _verdict(dataset.topics.exists(), "No topics"),
    ),
)
