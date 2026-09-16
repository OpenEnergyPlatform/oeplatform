<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# API Reference

Every endpoint of `api/v0` is described below, including the OEDB table and row
endpoints, the dataset endpoints and the OEKG scenario-bundle endpoints.

The description is **generated from the code**, not written by hand: it is
produced by `python manage.py spectacular` and committed to the repository as
[`openapi.yaml`](./openapi.yaml), so a pull request shows what the description
of the API became. A test in the suite regenerates it and fails if the committed
file has fallen behind, naming the command that brings it back in step.

!!! Info "This is the only description of `api/v0`"

    It used to share the job with a hand-written file behind the OEDB page.
    That file is gone: every endpoint it described is here, described from the
    code rather than by hand. The guides next to this page explain what the
    endpoints are *for* and link here for what they take.

!!! Info "OEP-API Token"

    Most write endpoints need authentication. Register at
    <https://openenergyplatform.org/accounts/signup/> or sign in with your
    institution, then find your API token on your profile page under the
    "Settings" tab.

    See the guide on
    [how to get started with the OpenEnergyPlatform](https://openenergyplatform.github.io/academy/courses/02_start/#how-do-i-get-started-with-the-oep).

The same description is served live by the running platform at
<https://openenergyplatform.org/api/v0/schema/>, and rendered there at
<https://openenergyplatform.org/api/v0/open-api/>.

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>API Documentation</title>
    <link rel="stylesheet" type="text/css" href="../dist/swagger-ui.css">
    <script src="../dist/swagger-ui-bundle.js"></script>
    <script src="../dist/swagger-ui-standalone-preset.js"></script>
</head>
<body>
<div id="swagger-ui"></div>
<script>
    window.onload = function() {
      // Initialize SwaggerUI
      const ui = SwaggerUIBundle({
        url: "../openapi.yaml",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout"
      })
    }
</script>
</body>
</html>
