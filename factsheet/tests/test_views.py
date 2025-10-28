"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase
from django.urls import reverse

from base.tests import get_app_reverse_lookup_names_and_kwargs


class TestViewsFactsheet(TestCase):
    """Call all (most) views"""

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        default_kwargs = {
            "bundle_id": "new",
            "scenarios_uid": "123",
            "entity_type": "region",
            "table_iri": "dataedit/view/scenario/abbb_emob",
        }

        errors = []
        for name, kwarg_names in sorted(
            get_app_reverse_lookup_names_and_kwargs("factsheet").items()
        ):

            if name in {
                "factsheet:add",  # requires POST
                "factsheet:delete",  # requires POST
                "factsheet:test-query",  # TODO: test query does not work
                "factsheet:all",  # TODO:  Temporary failure in name resolution>
                "factsheet:all-in-jsonld",  # TODO ???
                "factsheet:filter_bundles_view",  # TODO ???
                "factsheet:get",  # TODO ???
                "factsheet:get-entities-by-type",  # TODO ???
                "factsheet:get-scenarios",  # TODO ???
                "factsheet:populate-factsheets-elements",  # TODO ???
            }:
                continue

            try:
                kwargs = {k: default_kwargs[k] for k in kwarg_names}
                url = reverse(name, kwargs=kwargs)
                resp = self.client.get(path=url)
                self.assertTrue(resp.status_code < 400, msg=resp)
            except Exception as exc:
                errors.append(f"Failed view {name}: {exc}")

        if errors:
            raise Exception("\n".join(errors))
