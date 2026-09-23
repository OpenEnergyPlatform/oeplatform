"""The addresses `oedialect` needs from this platform must keep resolving.

`oedialect` is the SQLAlchemy dialect that lets people query the OEP as if it
were a database. It reaches the platform through `/api/v0/advanced/*` and
nowhere else, over plain HTTP -- so every one of those addresses is a public
contract, and renaming or removing one breaks every dialect user silently.

This is deliberately a *structural* test and not a behavioural one. It takes no
dependency on `oedialect` and starts no server: it asserts only that each
address the dialect asks for still reaches a view. Driving the real dialect
over HTTP is worth doing and belongs in that project's own CI, where it does
not enlarge this suite -- see the vault map "oedialect contract and CI".

What this catches is the likeliest break: somebody edits `api/urls.py` without
knowing who else is calling. What it cannot catch is a route that still
resolves and answers differently.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import SimpleTestCase
from django.urls import Resolver404, resolve

# Read off oedialect 0.1.1 on 2026-09-23, from the string literals it turns
# into URLs: `dialect.py` sets `query["command"] = "advanced/<name>"` and
# `engine.py` does `query.pop("command")` and makes it the path suffix, beside
# the calls that name their suffix directly.
#
# Add to this list when the dialect starts calling something new. Removing an
# entry is a decision about breaking a released client, not housekeeping.
OEDIALECT_ENDPOINTS = (
    "advanced/connection/open",
    "advanced/connection/close",
    "advanced/connection/commit",
    "advanced/connection/rollback",
    "advanced/cursor/open",
    "advanced/cursor/close",
    "advanced/cursor/fetch_one",
    "advanced/cursor/fetch_many",
    "advanced/cursor/fetch_all",
    "advanced/search",
    "advanced/insert",
    "advanced/update",
    "advanced/delete",
    "advanced/has_schema",
    "advanced/has_table",
    "advanced/has_sequence",
    "advanced/has_type",
    "advanced/get_schema_names",
    "advanced/get_table_names",
    "advanced/get_view_names",
    "advanced/get_view_definition",
    "advanced/get_columns",
    "advanced/get_pk_constraint",
    "advanced/get_foreign_keys",
    "advanced/get_indexes",
    "advanced/get_unique_constraints",
    "advanced/get_isolation_level",
    "advanced/set_isolation_level",
    "advanced/do_prepare_twophase",
    "advanced/do_commit_twophase",
    "advanced/do_rollback_twophase",
    "advanced/do_recover_twophase",
)

# Two of them have never been served. The dialect really does request these --
# `has_sequence` reaches them through `Sequence(...).create(checkfirst=True)`
# and reflection -- and gets a 404. They are pinned rather than fixed because
# whether to serve them or drop them from the dialect is a decision for the two
# projects together, not a side effect of writing this test.
KNOWN_UNSERVED = frozenset(
    {
        "advanced/has_sequence",
        "advanced/has_type",
    }
)


def unserved(endpoints):
    missing = set()
    for endpoint in endpoints:
        try:
            resolve("/api/v0/" + endpoint)
        except Resolver404:
            missing.add(endpoint)
    return missing


class OedialectContractTest(SimpleTestCase):
    def test_every_address_the_dialect_calls_still_resolves(self):
        served = [e for e in OEDIALECT_ENDPOINTS if e not in KNOWN_UNSERVED]

        self.assertEqual(
            set(),
            unserved(served),
            "an address oedialect calls no longer reaches a view; renaming or "
            "removing one breaks every dialect user with a 404",
        )

    def test_the_addresses_that_were_never_served_are_still_only_those_two(self):
        # Characterisation. Fails if a third goes missing -- and equally if one
        # of these two gets served, which is the good outcome and wants the
        # list updated rather than left lying.
        self.assertEqual(
            KNOWN_UNSERVED,
            unserved(OEDIALECT_ENDPOINTS),
            "the set of addresses oedialect calls but this platform does not "
            "serve has changed",
        )

    def test_the_contract_names_no_address_twice(self):
        self.assertEqual(
            len(OEDIALECT_ENDPOINTS),
            len(set(OEDIALECT_ENDPOINTS)),
            "a duplicate makes the list look larger than the contract is",
        )
