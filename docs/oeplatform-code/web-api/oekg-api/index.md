## OEKG web based access

In this document we describe how you can access the contents of the OEKG via Web based Requests using HTTP

### The SPARQL endpoint for OEKG

`https://openenergyplatform.org/oekg/sparql/`

Here is an example of how to query the Open Energy Knowledge Graph (OEKG) using SPARQL using python and the requests library for http requests.

```python
import requests

sparql_endpoint = "https://openenergy-platform.org/oekg/sparql/"
payload = {
    "query": """SELECT ?s ?p ?o
                WHERE {
                  ?s ?p ?o
                }"""
    "format": "json-ld"
}

r = requests.post(url=sparql_endpoint, json=payload)
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
