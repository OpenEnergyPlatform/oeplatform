from api import actions

from .error import MetadataException


def from_v0(comment_on_table, schema, table):
    columns = actions.analyze_columns(schema, table)
    refdate = comment_on_table["Reference date"]
    try:
        if "resources" not in comment_on_table:
            comment_on_table = {
                "title": comment_on_table["Name"],
                "description": "; ".join(comment_on_table["Description"]),
                "language": [],
                "reference_date": refdate[0] if isinstance(refdate, list) else refdate,
                "spatial": [
                    {"extent": x, "resolution": ""}
                    for x in comment_on_table["Spatial resolution"]
                ],
                "temporal": [
                    {"start": x, "end": "", "resolution": ""}
                    for x in comment_on_table.get("Temporal resolution", [])
                ],
                "sources": [
                    {
                        "name": x["Name"],
                        "description": "",
                        "url": x["URL"],
                        "license": " ",
                        "copyright": " ",
                    }
                    for x in comment_on_table.get("Source", [])
                ],
                "license": [
                    {
                        "id": "",
                        "name": x,
                        "version": "",
                        "url": "",
                        "instruction": "",
                        "copyright": "",
                    }
                    for x in comment_on_table.get("Licence", [])
                ],
                "contributors": [
                    {
                        "name": x["Name"],
                        "email": x["Mail"],
                        "date": x["Date"],
                        "comment": x["Comment"],
                    }
                    for x in comment_on_table.get("Changes", [])
                ],
                "resources": [
                    {
                        "name": "",
                        "format": "sql",
                        "fields": [
                            {
                                "name": x["Name"],
                                "description": x["Description"],
                                "unit": x["Unit"],
                            }
                            for x in comment_on_table.get("Column", [])
                        ],
                    }
                ],
                "meta_version": "1.1",
            }

            comment_on_table["fields"] = comment_on_table["resources"][0]["fields"]

            commented_cols = [col["name"] for col in comment_on_table["fields"]]
        else:
            comment_on_table["fields"] = comment_on_table["resources"][0]["fields"]

            if "fields" not in comment_on_table["resources"][0]:
                comment_on_table["fields"] = []
            else:
                comment_on_table["fields"] = comment_on_table["resources"][0]["fields"]

            commented_cols = [col["name"] for col in comment_on_table["fields"]]
    except Exception as e:
        raise MetadataException(comment_on_table, e)

    for col in columns:
        if not col["id"] in commented_cols:
            comment_on_table["fields"].append(
                {"name": col["id"], "description": "", "unit": ""}
            )

    return comment_on_table
