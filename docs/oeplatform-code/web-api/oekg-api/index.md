<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# The OEKG SPARQL endpoint

The Open Energy Knowledge Graph is reachable over HTTP in two ways, and this
page is about the first of them:

- **SPARQL**, below: one endpoint, read-only, for asking the graph questions.
- **The scenario-bundle endpoints**, for creating and changing bundles, their
  scenarios, study reports and dataset links. Those are described in the
  [API Reference](../api-reference.md) with the rest of `api/v0`, and they are
  the only way to _write_ to the graph through this API — the SPARQL endpoint
  refuses an update whatever the caller's permissions, because a write has to be
  validated against the OEKG shape and a passthrough cannot do that.

## The SPARQL endpoint

`https://openenergyplatform.org/api/v0/oekg/sparql/`

Here is an example of how to query the Open Energy Knowledge Graph (OEKG) using
SPARQL using python and the requests library for http requests.

!!! Info "OEP-API Token"

    For authentication with the OEP-REST-API you have to register on <https://openenergyplatform.org/accounts/signup/> or sign in with you institution.
    Once you are registered you can find your API Token in you Profile page under the "Settings" Tab. Clicks "Show Token" and copy the hash value.

    See our more detailed guide on [how to get started with the OpenEnergyPlatform](https://openenergyplatform.github.io/academy/courses/02_start/#how-do-i-get-started-with-the-oep).

```python
import requests

OEP_API_TOKEN = "<Add-Your-Token>"
HEADER = {"Authorization": f"Token {OEP_API_TOKEN}"}
sparql_endpoint = "https://openenergyplatform.org/api/v0/oekg/sparql/"
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

## Writing to the graph

Not here. The endpoint above is a passthrough: it hands a query to the graph
store and returns what comes back, and an update or delete is refused. Creating
and changing scenario bundles is done through the scenario-bundle endpoints in
the [API Reference](../api-reference.md), which validate every write against the
OEKG shape, guard it with an `If-Match` version, and record it in the bundle's
history.
