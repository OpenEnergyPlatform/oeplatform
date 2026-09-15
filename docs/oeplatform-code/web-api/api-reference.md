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

!!! Info "Two descriptions of the OEDB endpoints"

    The [OEDB REST-API](./oedb-rest-api/index.md) page embeds an older,
    hand-written description of the table and row endpoints, and it is kept for
    now: the two are complementary rather than one superseding the other. This
    page is generated, so it is complete about *which* endpoints exist; but the
    OEDB views are not yet annotated, so it reports them without request or
    response bodies, and the handful routed by regular expression rather than by
    path appear here with that expression still in the address. The hand-written
    page carries the bodies and the readable addresses, and can be out of date
    about what is routed. Read them together until the OEDB endpoints are
    annotated.

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
