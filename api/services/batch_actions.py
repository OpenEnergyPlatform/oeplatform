"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

What every action service of the profile dashboard shares (spec #2613): the
words of the preflight/execute contract, whatever the service acts on. The
table action service (``api.services.table_actions``) and the Dataset action
service (``api.services.dataset_actions``) each subclass and import these
rather than stating them twice.

- ``LeftOut``: items an action would not touch, grouped by reason.
- ``ActionError`` and its two kinds: ``InvalidParameters`` (a parameter is
  unusable) and ``ActionRefused`` (an item is no longer allowed, so nothing
  was written).
- ``Preflight``: the core of what a preflight returns, with the ceiling it
  states. A service subclasses it, naming its nouns and its actions' names
  (``item``, ``items``, ``action_names``) and adding its own fields.
- ``unique``, ``quoted``, ``choice`` and the messages for a batch's subject,
  its ceiling and a typed confirmation, each taking the noun it speaks of;
  ``typed_confirmation``, what a delete asks the user to type.

An item is anything with a ``name``: a Table, a Dataset.
"""  # noqa: 501

from dataclasses import dataclass, field
from typing import ClassVar

# A batch of more than this many items is confirmed by typing its count.
TYPED_COUNT_ABOVE = 10


class ActionError(Exception):
    """Base of the two ways ``execute`` can decline."""


class InvalidParameters(ActionError):
    """A parameter of the request is unusable; ``errors`` maps each
    parameter to what is wrong with it. Nothing was written."""

    def __init__(self, errors: dict):
        super().__init__("; ".join(errors.values()))
        self.errors = errors


class ActionRefused(ActionError):
    """At least one named item is no longer allowed, so nothing was
    written. ``refused`` is the left-out groups that caused it, and
    ``preflight`` the check as it stands now.

    ``role_refusals`` are the left-out reasons that mean "you lack the role";
    a service's subclass names them, and ``for_role`` reads them."""

    role_refusals: frozenset = frozenset()

    def __init__(self, preflight: "Preflight", refused: list):
        self.preflight = preflight
        self.refused = refused
        super().__init__(self.message)

    @property
    def message(self) -> str:
        parts = [f"{group.reason} ({quoted(group.names)})" for group in self.refused]
        return "Nothing was changed: " + "; ".join(parts) + "."

    @property
    def for_role(self) -> bool:
        """Whether an item was refused because the user lacks the role the
        action needs there (or holds none at all), rather than because the
        items changed."""
        return any(group.reason in self.role_refusals for group in self.refused)


@dataclass(frozen=True)
class LeftOut:
    """Items an action would not touch, all for the same reason. The
    reason is the text the user is shown."""

    reason: str
    names: list


@dataclass
class Preflight:
    """What ``execute`` would do with these names, before it does it.

    ``eligible`` are the items it would act on, in the order named;
    ``left_out`` the rest, grouped by reason. ``ceiling`` is the most items
    the action takes in one request, None where no limit is set;
    ``over_ceiling`` says the names sent exceed it, and then nothing can be
    confirmed. ``consequences`` holds what the dialog has to state for this
    action, and ``subject`` is what the request is about: the one item's
    title, or for a batch the items it acts on (``batch_subject``: "n
    tables", or "e of n tables" when some are not acted on).
    ``confirmation`` is what the user has to type to confirm, "" for a plain
    confirmation.

    A service's subclass sets ``item`` and ``items`` (the noun, singular and
    plural; as properties where the noun depends on the action) and
    ``action_names`` (each action at the start of a sentence).
    """

    item: ClassVar[str] = "item"
    items: ClassVar[str] = "items"
    action_names: ClassVar[dict] = {}

    action: str
    total: int
    eligible: list
    left_out: list
    ceiling: int = None
    consequences: dict = field(default_factory=dict)
    subject: str = ""
    confirmation: str = ""
    # every name sent, once each, in the order sent: what a bulk dialog
    # re-checks when the user chooses in it, so the left-out groups stay
    # complete although the form posts only the eligible names
    requested: list = field(default_factory=list)

    @property
    def names(self) -> list:
        return [item.name for item in self.eligible]

    @property
    def left_out_count(self) -> int:
        """How many of the names sent are left out, over every reason."""
        return sum(len(group.names) for group in self.left_out)

    @property
    def over_ceiling(self) -> bool:
        return self.ceiling is not None and self.total > self.ceiling

    @property
    def ceiling_message(self) -> str:
        return ceiling_message(
            self.action_names[self.action], self.ceiling, self.total, self.items
        )

    @property
    def ceiling_rule(self) -> str:
        """The ceiling as the dialog states it before anything exceeds it,
        "" where the action has none."""
        if not self.ceiling:
            return ""
        return ceiling_rule(self.action_names[self.action], self.ceiling, self.items)


def quoted(names) -> str:
    return ", ".join(f"“{name}”" for name in names)


def unique(names) -> list:
    """``names`` once each, in the order sent, without empty ones."""
    return list(dict.fromkeys(name for name in names if name))


def choice(keys, params) -> str:
    """The parameters ``keys`` of ``params`` as one string: the choice a
    dialog made, which its preview carries as ``previewed`` and a
    confirmation's own parameters are compared with."""
    return ",".join(str(params.get(key) or "") for key in keys)


def batch_subject(acted_on, total, items) -> str:
    """What a batch's dialog is about, counting what its list counts: the
    ``items`` the action would act on, out of the names sent when that is
    fewer ("14 of 16 tables"), so the title and the list agree and the
    left-out difference shows in the title."""
    if acted_on == total:
        return f"{total:,} {items}"
    return f"{acted_on:,} of {total:,} {items}"


def ceiling_rule(action_name, ceiling, items) -> str:
    return f"{action_name} takes at most {ceiling:,} {items} at a time."


def ceiling_message(action_name, ceiling, total, items) -> str:
    return f"{ceiling_rule(action_name, ceiling, items)[:-1]}; you selected {total:,}."


def typed_confirmation(eligible, published) -> str:
    """What the user has to type to confirm a delete of ``eligible``, or ""
    for a plain confirmation: the item's name for one published item, the
    number of items for a batch holding a published one or more than
    ``TYPED_COUNT_ABOVE``. ``published`` says whether an item is."""
    if not eligible:
        return ""
    any_published = any(published(item) for item in eligible)
    if len(eligible) == 1:
        return eligible[0].name if any_published else ""
    if any_published or len(eligible) > TYPED_COUNT_ABOVE:
        return str(len(eligible))
    return ""


def confirm_error(check) -> str:
    """What a typed confirmation that does not match ``check.confirmation``
    is told: the item's name for one, the count for a batch."""
    if check.total == 1:
        return f"Type the {check.item}'s name, {check.confirmation}, to confirm."
    return f"Type the number of {check.items}, {check.confirmation}, to confirm."
