"""
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from copy import deepcopy
from datetime import datetime

import requests
from oemetadata.latest.template import OEMETADATA_LATEST_TEMPLATE
from shapely import wkt
from shapely.geometry import base as shapely_geom_base

from oeplatform.securitysettings import SCHEMA_DATA

# === CONFIG ===

PROD_BASE = "https://openenergyplatform.org/api/v0"
LOCAL_BASE = "http://127.0.0.1:8000/api/v0"

PROD_TOKEN = ""  # UPDATE: Set your production API token here
LOCAL_TOKEN = ""  # UPDATE: Set your local API token here

CHUNK_SIZE = 1000
SKIP_GEOMETRY_COLUMNS = False  # Now we include geometry, converted to GeoJSON
LOCAL_SCHEMA = SCHEMA_DATA

TABLES_TO_COPY = [
    {
        "schema": "scenario",
        "table": "eu_leg_data_2021_rep_table_1",
        "publish_to": "scenario",
    },
]

# Example of how to copy multiple tables
# TABLES_TO_COPY = [
#     {"schema": "grid", "table": "ego_grid_ding0_mv_grid", "publish_to": "grid"},
#     {
#         "schema": "grid",
#         "table": "ego_grid_ding0_hvmv_transformer",
#         "publish_to": "grid",
#     },
#     {"schema": "grid", "table": "ego_grid_ding0_line", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_lv_branchtee", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_lv_generator", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_lv_grid", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_lv_load", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_lv_station", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_mv_branchtee", "publish_to": "grid"},
#     {
#         "schema": "grid",
#         "table": "ego_grid_ding0_mv_circuitbreaker",
#         "publish_to": "grid",
#     },
#     {"schema": "grid", "table": "ego_grid_ding0_mv_generator", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_mv_load", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_mv_station", "publish_to": "grid"},
#     {"schema": "grid", "table": "ego_grid_ding0_mvlv_mapping", "publish_to": "grid"},
#     {
#         "schema": "grid",
#         "table": "ego_grid_ding0_mvlv_transformer",
#         "publish_to": "grid",
#     },
#     {"schema": "grid", "table": "ego_grid_ding0_versioning", "publish_to": "grid"},
# ]


# === REQUEST HANDLER ===
def api_request(method, url, json=None):
    token = PROD_TOKEN if url.startswith(PROD_BASE) else LOCAL_TOKEN
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    if method == "get":
        return requests.get(url, headers=headers)
    elif method == "post":
        return requests.post(url, headers=headers, json=json)
    elif method == "put":
        return requests.put(url, headers=headers, json=json)
    else:
        raise ValueError(f"Unsupported method: {method}")


# === CORE FUNCTIONS ===
def get_column_definitions(schema, table):
    url = f"{PROD_BASE}/schema/{schema}/tables/{table}/columns/"
    r = api_request("get", url)
    r.raise_for_status()
    return r.json()


def transform_columns_for_query(column_definitions):
    columns = []
    for name, col in column_definitions.items():
        if col["data_type"] == "geometry":
            continue  # Geometry will be added via function result
        col_def = {
            "name": name,
            "data_type": map_data_type(
                col["data_type"], col["character_maximum_length"]
            ),
            "is_nullable": col["is_nullable"],
        }
        if name == "id":
            col_def["primary_key"] = True
        columns.append(col_def)
    columns.append(
        {  # Add new column for geometry as GeoJSON
            "name": "geom_geojson",
            "data_type": "text",
            "is_nullable": True,
        }
    )
    return columns


def map_data_type(dtype, length):
    if dtype == "character varying":
        return f"varchar({length})" if length else "text"
    elif dtype == "character":
        return f"varchar({length})" if length else "text"
    elif dtype == "integer":
        return "int"
    elif dtype == "bigint":
        return "bigint"
    elif dtype == "real":
        return "float"
    elif dtype == "numeric":
        return "numeric"
    elif dtype == "boolean":
        return "boolean"
    elif dtype == "timestamp without time zone":
        return "timestamp"
    elif dtype == "double precision":
        return "numeric"
    return dtype


def create_table(schema, table, column_definitions):
    url = f"{LOCAL_BASE}/schema/{schema}/tables/{table}/"
    table_schema = {"columns": transform_columns_for_query(column_definitions)}
    response = api_request("put", url, json={"query": table_schema})
    if response.status_code == 409:
        print(f"[{schema}.{table}] Already exists.")
    if response.status_code == 400:
        print(f"[{schema}.{table}] Already exists.")

    else:
        response.raise_for_status()
        print(f"[{schema}.{table}] Created.")


def fetch_table_rows(schema, table):
    """
    Fetch rows via the OEPs REST-API from a table using advanced
    search with ST_AsGeoJSON for geometry.

    Args:
        schema (str): The schema name.
        table (str): The table name.
    Returns:
        tuple: A tuple containing a list of rows and a list of field names.

    """
    print(f"[{schema}.{table}] Fetching rows using advanced search + ST_AsGeoJSON...")
    url = f"{PROD_BASE}/advanced/search"

    # Get columns (again) to build a proper field list
    column_defs = get_column_definitions(schema, table)
    fields = []

    for name, col in column_defs.items():
        if col["data_type"] != "geometry":
            fields.append({"type": "column", "column": name})

    # Add geometry as GeoJSON if present
    if "geom" in column_defs:
        fields.append(
            {
                "type": "function",
                "function": "ST_AsGeoJSON",
                "operands": [{"type": "column", "column": "geom"}],
                "as": "geom_geojson",
            }
        )

    query = {
        "fields": fields,
        "from": {"type": "table", "schema": schema, "table": table},
        "limit": CHUNK_SIZE,
        "offset": 0,
    }

    r = api_request("post", url, json={"query": query})
    r.raise_for_status()
    result = r.json()
    rows = result.get("data", [])

    field_names = []
    for f in query["fields"]:
        if isinstance(f, str):
            field_names.append(f)
        elif isinstance(f, dict) and "as" in f:
            field_names.append(f["as"])
        elif isinstance(f, dict) and f.get("type") == "column" and "column" in f:
            field_names.append(f["column"])
        else:
            raise ValueError(f"Can't determine field name for field: {f}")

    return rows, field_names


def convert_row_to_json_dict(row, fields):
    item = {}
    for i, value in enumerate(row):
        key = fields[i]

        if isinstance(value, datetime):
            item[key] = value.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(value, shapely_geom_base.BaseGeometry):
            item[key] = wkt.dumps(value)
        else:
            item[key] = value
    return item


def insert_rows(schema, table, rows, fields):
    if not rows:
        print(f"[{schema}.{table}] No rows to insert.")
        return

    url = f"{LOCAL_BASE}/schema/{schema}/tables/{table}/rows/new"
    total = len(rows)
    for i in range(0, total, CHUNK_SIZE):
        chunk_rows = rows[i : i + CHUNK_SIZE]
        dict_rows = [convert_row_to_json_dict(r, fields) for r in chunk_rows]
        payload = {"query": dict_rows}
        r = api_request("post", url, json=payload)
        if not r.ok:
            print("❌ Insert failed:", r.status_code, r.text)
        else:
            print(
                f"[{schema}.{table}] Inserted"
                f"{len(dict_rows)} rows ({i + len(dict_rows)}/{total})"
            )


def add_oemetadata(schema, table):
    url = f"{LOCAL_BASE}/schema/{schema}/tables/{table}/meta/"
    metadata = deepcopy(OEMETADATA_LATEST_TEMPLATE)
    metadata["license"] = "https://www.opendefinition.org/licenses/cc-by/"
    r = api_request("post", url, json=metadata)
    r.raise_for_status()
    print(f"[{schema}.{table}] Metadata attached.")


def publish_table(from_schema, table, to_schema):
    url = f"{LOCAL_BASE}/schema/{from_schema}/tables/{table}/move/{to_schema}/"
    r = api_request("post", url)
    r.raise_for_status()
    print(f"✅ Published {table} → {to_schema}")


def copy_table(remote_schema, table, publish_to):
    print(f"\n🔄 Copying {remote_schema}.{table} to {LOCAL_SCHEMA}.{table}...")
    col_meta = get_column_definitions(remote_schema, table)
    create_table(LOCAL_SCHEMA, table, col_meta)
    rows, fields = fetch_table_rows(remote_schema, table)
    insert_rows(LOCAL_SCHEMA, table, rows, fields)
    add_oemetadata(LOCAL_SCHEMA, table)
    publish_table(LOCAL_SCHEMA, table, publish_to)


# === MAIN RUN ===
if __name__ == "__main__":
    for entry in TABLES_TO_COPY:
        copy_table(entry["schema"], entry["table"], publish_to=entry["publish_to"])

    print("\n✅ All tables processed (with ST_AsGeoJSON if geometry present).")
