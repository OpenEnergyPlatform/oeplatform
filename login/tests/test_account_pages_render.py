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

The template offers the NFDI RegApp only when its OEP_REGAPP_* variables are
set (as `oep.env` does on a Podman server), so both cases are rendered.
"""  # noqa: 501

import runpy
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

TEMPLATE = Path(settings.BASE_DIR) / "oeplatform" / "securitysettings.py.default"


REGAPP = {
    "OEP_REGAPP_CLIENT_ID": "client",
    "OEP_REGAPP_SECRET": "secret",
    "OEP_REGAPP_SERVER_URL": "https://regapp.example/.well-known/openid-configuration",
}


def template_setting(name, environ):
    with mock.patch.dict("os.environ", environ, clear=True):
        return runpy.run_path(str(TEMPLATE))[name]


class AccountPagesRenderTest(TestCase):
    def assert_pages_render(self, providers):
        with override_settings(SOCIALACCOUNT_PROVIDERS=providers):
            for name in ("account_signup", "account_login"):
                with self.subTest(page=name):
                    response = self.client.get(reverse(name))
                    self.assertEqual(response.status_code, 200)
        return response

    def test_without_a_provider_configured(self):
        providers = template_setting("SOCIALACCOUNT_PROVIDERS", {})
        self.assertEqual(providers["openid_connect"]["APPS"], [])
        self.assert_pages_render(providers)

    def test_with_the_regapp_configured(self):
        providers = template_setting("SOCIALACCOUNT_PROVIDERS", REGAPP)
        (app,) = providers["openid_connect"]["APPS"]
        self.assertEqual(app["client_id"], "client")
        self.assertEqual(app["settings"]["server_url"], REGAPP["OEP_REGAPP_SERVER_URL"])
        self.assertNotIn("verified_email", app["settings"])
        response = self.assert_pages_render(providers)
        self.assertContains(response, "/accounts/oidc/RegApp/login/")
