<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

## OEKG web based access

In this document we describe how you can access the contents of the OEKG via Web based Requests using HTTP

### The SPARQL endpoint for OEKG

`https://openenergyplatform.org/api/v0/oekg/sparql/`

Here is an example of how to query the Open Energy Knowledge Graph (OEKG) using SPARQL using python and the requests library for http requests.

!!! Info "OEP-API Token"

    For authentication with the OEP-REST-API you have to register on <https://openenergyplatform.org/accounts/signup/> or sign in with you institution.
    Once you are registered you can find your API Token in you Profile page under the "Settings" Tab. Clicks "Show Token" and copy the hash value.

    See our more detailed guide on [how to get started with the OpenEnergyPlatform](https://openenergyplatform.github.io/academy/courses/02_start/#how-do-i-get-started-with-the-oep).

```python
import requests

OEP_API_TOKEN = "<Add-Your-Token>"
HEADER = {"Authorization": f"Token {OEP_API_TOKEN}"}
sparql_endpoint = "https://openenergy-platform.org/api/v0/oekg/sparql/"
payload = {
    "query": """SELECT ?s ?p ?o
                WHERE {
                  ?s ?p ?o
                }""",
    "format": "json"
}

r = requests.post(url=sparql_endpoint, json=payload, headers=HEADER)
print(r.json())
```

## Open API

Below you see a draft version of the OpenAPI-based. It is the documentation for all HTTP-API endpoints and in the future it can be used to test out the API.

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
        url: "./oekg.yaml",
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
