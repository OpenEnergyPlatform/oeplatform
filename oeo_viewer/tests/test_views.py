"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from django.test import TestCase
from django.urls import reverse

from base.tests import get_app_reverse_lookup_names_and_kwargs


class TestViewsOeoViewer(TestCase):
    """Call all (most) views"""

    def test_views(self):
        """Call all (most) views that can be found with reverse lookup.
        We only test method GET
        """

        default_kwargs = {}

        for name, kwarg_names in sorted(
            get_app_reverse_lookup_names_and_kwargs("oeo_viewer").items()
        ):

            errors = []
            try:
                kwargs = {k: default_kwargs[k] for k in kwarg_names}
                url = reverse(name, kwargs=kwargs)
                resp = self.client.get(path=url)
                self.assertTrue(resp.status_code < 400)
            except Exception as exc:
                errors.append(f"Failed view {name}: {exc}")

        if errors:
            raise Exception("\n".join(errors))
