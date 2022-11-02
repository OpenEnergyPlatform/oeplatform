from api import actions

from . import v1_1


def from_v1_1(comment_on_table, schema, table):
    columns = actions.analyze_columns(schema, table)
    try:
        if "resources" not in comment_on_table:
            comment_on_table = {
                "title": comment_on_table["Name"],
                "description": "; ".join(comment_on_table["Description"]),
                "language": [],
                "reference_date": comment_on_table["Reference date"],
                "sources": [
                    {
                        "name": x["Name"],
                        "description": "",
                        "url": x["URL"],
                        "license": " ",
                        "copyright": " ",
                    }
                    for x in comment_on_table["Source"]
                ],
                "spatial": [
                    {"extend": x, "resolution": ""}
                    for x in comment_on_table["Spatial resolution"]
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
                    for x in comment_on_table["Licence"]
                ],
                "contributors": [
                    {
                        "name": x["Name"],
                        "email": x["Mail"],
                        "date": x["Date"],
                        "comment": x["Comment"],
                    }
                    for x in comment_on_table["Changes"]
                ],
                "resources": [
                    {
                        "schema": {
                            "fields": [
                                {
                                    "name": x["Name"],
                                    "description": x["Description"],
                                    "unit": x["Unit"],
                                }
                                for x in comment_on_table["Column"]
                            ]
                        },
                        "meta_version": "1.2",
                    }
                ],
            }

            comment_on_table["fields"] = comment_on_table["resources"][0]["schema"][
                "fields"
            ]

            commented_cols = [col["name"] for col in comment_on_table["fields"]]
        else:
            comment_on_table["resources"] = [
                {"schema": x} for x in comment_on_table["resources"]
            ]
            if "fields" not in comment_on_table["resources"][0]:
                comment_on_table["fields"] = []
            else:
                comment_on_table["fields"] = comment_on_table["resources"][0]["fields"]

            commented_cols = [col["name"] for col in comment_on_table["fields"]]
    except Exception:
        comment_on_table = {"description": comment_on_table, "fields": []}
        commented_cols = []

    for col in columns:
        if not col["id"] in commented_cols:
            comment_on_table["fields"].append(
                {"name": col["id"], "description": "", "unit": ""}
            )

    return comment_on_table


def from_v0(comment_on_table, schema, table):
    return from_v1_1(v1_1.from_v0(comment_on_table, schema, table), schema, table)
