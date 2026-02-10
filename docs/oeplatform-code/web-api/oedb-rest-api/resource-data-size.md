<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Database Table Sizes

Short guide for the **Table Sizes** API endpoint. This endpoint returns the
storage size of individual tables (including indexes) or all tables across all
schemas.

> Base URL: `https://openenergyplatform.org`

## Authentication

This endpoint requires token authentication.

```http
Authorization: Token <YOUR_API_TOKEN>
```

!!! warning "Security"

    Never use real tokens in documentation. Always use placeholders like `<YOUR_API_TOKEN>`.

## Endpoint

```
GET /api/v0/db/table-sizes/
```

### Query Parameters

| Parameter | Type | Description                                                                     |
| --------- | ---- | ------------------------------------------------------------------------------- |
| `schema`  | str  | optional; filter by schema                                                      |
| `table`   | str  | optional; filter by a specific table (only useful in combination with `schema`) |

## Examples

### All Tables (all Schemas)

```bash
curl -s \
  -H "Authorization: Token <YOUR_API_TOKEN>" \
  "https://openenergyplatform.org/api/v0/db/table-sizes/"
```

### Single Table

```bash
curl -s \
  -H "Authorization: Token <YOUR_API_TOKEN>" \
  "https://openenergyplatform.org/api/v0/db/table-sizes/?table=oeko_testtable"
```

### Raw HTTP Example

```http
GET /api/v0/db/table-sizes/?table=oeko_testtable HTTP/1.1
Host: openenergyplatform.org
Authorization: Token <YOUR_API_TOKEN>
```

## Example Response

```json
{
  "table_name": "oeko_testtable",
  "table_bytes": 0,
  "index_bytes": 0,
  "total_bytes": 8192,
  "table_pretty": "0 bytes",
  "index_pretty": "0 bytes",
  "total_pretty": "8192 bytes"
}
```

!!! note "Note on empty tables"

    `8192` bytes is typically the default overhead for an empty table (one memory page). Therefore, `total_bytes` can be > 0 even if `table_bytes` and `index_bytes` are zero.

## Response Fields

| Field          | Type | Description                                              |
| -------------- | ---- | -------------------------------------------------------- |
| `table_schema` | str  | Name of the schema                                       |
| `table_name`   | str  | Table name                                               |
| `table_bytes`  | int  | Size of the table data in bytes                          |
| `index_bytes`  | int  | Size of the associated indexes in bytes                  |
| `total_bytes`  | int  | Sum of `table_bytes` + `index_bytes` + possible overhead |
| `table_pretty` | str  | Human-readable representation of `table_bytes`           |
| `index_pretty` | str  | Human-readable representation of `index_bytes`           |
| `total_pretty` | str  | Human-readable representation of `total_bytes`           |

## Error Cases

- `401 Unauthorized`: Token missing or invalid.
- `400 Bad Request`: Invalid parameter combination (e.g., `table` without
  `schema`).

## Quickstart in Python (requests)

```python
import requests

BASE_URL = "https://openenergyplatform.org/api/v0/db/table-sizes/"
HEADERS = {"Authorization": "Token <YOUR_API_TOKEN>"}

# All tables
r = requests.get(BASE_URL, headers=HEADERS)
r.raise_for_status()
print(r.json())

# Single table
params = {"table": "testtable"}
r = requests.get(BASE_URL, headers=HEADERS, params=params)
r.raise_for_status()
print(r.json())
```

---

_Last updated: 17.08.2025_
