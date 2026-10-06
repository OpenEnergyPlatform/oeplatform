"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The sign-in and sign-up pages render with the login providers that
`oeplatform/securitysettings.py.default` configures.

Both pages render a login link per configured provider. The template used to
list an openid_connect app with an empty `provider_id`, for which no login URL
can be built, so every setup copied from it (CI, the docker and podman
entrypoints, a fresh dev instance) answered both pages with a 500. The test
reads the template itself, so it guards it on a machine with a real provider
too.
"""  # noqa: 501

import ast
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

TEMPLATE = Path(settings.BASE_DIR) / "oeplatform" / "securitysettings.py.default"


def template_setting(name):
    for node in ast.parse(TEMPLATE.read_text()).body:
        if isinstance(node, ast.Assign) and any(
            getattr(target, "id", None) == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise LookupError(f"{name} is not set in {TEMPLATE}")


class AccountPagesRenderTest(TestCase):
    def test_with_the_templates_login_providers(self):
        with override_settings(
            SOCIALACCOUNT_PROVIDERS=template_setting("SOCIALACCOUNT_PROVIDERS")
        ):
            for name in ("account_signup", "account_login"):
                with self.subTest(page=name):
                    self.assertEqual(self.client.get(reverse(name)).status_code, 200)
