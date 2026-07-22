"""
Pure metadata-shaping functions for the Open Peer Review templates.

SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

Extracted verbatim from ``dataedit.views.TablePeerReviewView`` (Phase 2, step
S1). These functions are pure (no DB, no request) so they can be unit-tested in
isolation and keep the view thin. Behavior is intentionally identical to the
previous inline methods; the only signature change is that ``sort_in_category``
no longer takes the unused ``table`` argument.
"""  # noqa: E501

import re
from collections import defaultdict


def parse_keys(val, old=""):
    """
    Recursively parse keys from a nested dictionary or list and return them
    as a list of dictionaries.

    Args:
        val (dict or list): The input dictionary or list to parse.
        old (str, optional): The prefix for nested keys. Defaults to an
            empty string.

    Returns:
        list: A list of dictionaries, each containing 'field' and 'value'
            keys.
    """
    lines = []
    if isinstance(val, dict):
        for k in val.keys():
            lines += parse_keys(val[k], old + "." + str(k))
    elif isinstance(val, list):
        if not val:
            # handles empty list
            lines += [{"field": old[1:], "value": str(val)}]
        else:
            for i, k in enumerate(val):
                lines += parse_keys(k, old + "." + str(i))  # handles user value
    else:
        lines += [{"field": old[1:], "value": str(val)}]
    return lines


def sort_in_category(oemetadata):
    """
    Groups OEMetadata v2 fields by top categories and creates a two-level
    grouping of lists (accordion-within-an-accordion) for general, source,
    license, and spatial/temporal.

    Category Exit:
        {"flat":    [ { field, value, label, display_field, newValue,
         reviewer_suggestion, suggestion_comment, ... } ],
          "grouped": { "<Name N>": { "flat":[...], "grouped":{ "<Sub N>":[...]
          } }, ... }
        }
    """

    def _plus_one_if_digit(txt: str) -> str:
        return str(int(txt) + 1) if str(txt).isdigit() else txt

    flattened = parse_keys(oemetadata)
    flattened = [
        x for x in flattened if str(x.get("field", "")).startswith("resources.")
    ]

    base_items = []
    for item in flattened:
        raw = item["field"]
        parts = raw.split(".")
        if len(parts) >= 3 and parts[0] == "resources" and parts[1].isdigit():
            trimmed = ".".join(parts[2:])
        else:
            trimmed = raw

        lbl_parts = [p.replace("_", " ") for p in trimmed.split(".")]
        if lbl_parts:
            lbl_parts[0] = lbl_parts[0][:1].upper() + lbl_parts[0][1:]
        label = " ".join(lbl_parts)

        base_items.append(
            {
                "field": trimmed,
                "label": label,
                "value": item.get("value", ""),
                "newValue": "",
                "reviewer_suggestion": "",
                "suggestion_comment": "",
                "additional_comment": item.get("additional_comment", ""),
            }
        )

    main_categories = defaultdict(list)
    for itm in base_items:
        root = itm["field"].split(".")[0] if "." in itm["field"] else itm["field"]
        cat = {
            "spatial": "spatial",
            "temporal": "temporal",
            "sources": "source",
            "licenses": "license",
        }.get(root, "general")
        main_categories[cat].append(itm)

    def extract_index(prefix: str) -> int:
        m = re.search(r"(?:\.|\s)([0-9]+)$", prefix or "")
        return int(m.group(1)) if m else -1

    def group_index_only(items):
        """First index occurrence: name.0.* → 'Name 1';
        otherwise, group by the first token."""
        result = {"flat": [], "grouped": defaultdict(list)}
        for itm in items:
            field = itm["field"]
            m = re.match(r"^([^.]+)\.([0-9]+)(?:\.(.*))?$", field)
            if m:
                list_name, idx, tail = (
                    m.group(1),
                    int(m.group(2)),
                    m.group(3) or "value",
                )
                disp_prefix = f"{list_name.capitalize()} {idx + 1}"
                enriched = dict(itm)
                enriched["display_field"] = tail
                enriched["display_prefix"] = disp_prefix
                enriched["display_index"] = str(idx + 1)
                result["grouped"][disp_prefix].append(enriched)
            elif "." in field:
                group_key = field.split(".")[0]
                enriched = dict(itm)
                enriched["display_field"] = ".".join(field.split(".")[1:])
                enriched["display_prefix"] = group_key
                enriched.pop("display_index", None)
                result["grouped"][group_key].append(enriched)
            else:
                enriched = dict(itm)
                enriched["display_field"] = field
                enriched.pop("display_index", None)
                result["flat"].append(enriched)
        result["grouped"] = dict(
            sorted(result["grouped"].items(), key=lambda kv: extract_index(kv[0]))
        )
        return result

    def nest_sublist_groups(items_for_one_parent):
        grouped_map = defaultdict(lambda: {"flat": [], "grouped": {}})
        flat = []

        for itm in items_for_one_parent:
            field = itm["field"]
            m = re.match(r"^([^.]+)\.([0-9]+)(?:\.(.*))?$", field)
            if m:
                head, idx, tail = m.group(1), int(m.group(2)), m.group(3)
                e = dict(itm)
                e["display_field"] = tail if (tail and tail.strip()) else str(idx)
                e["display_prefix"] = head
                e.pop("display_index", None)
                grouped_map[head.capitalize()]["flat"].append(e)
            else:
                e = dict(itm)
                trimmed = ".".join(field.split(".")[1:]) if "." in field else field
                e["display_field"] = _plus_one_if_digit(trimmed)
                flat.append(e)

        grouped = dict(sorted(grouped_map.items(), key=lambda kv: kv[0]))
        return {"flat": flat, "grouped": grouped}

    def _strip_cat_prefix(items, cat_name):
        """spatial.extent.name → extent.name; temporal.period.start →
        period.start"""
        out = []
        for it in items:
            f = it["field"]
            if f.startswith(cat_name + "."):
                trimmed = f[len(cat_name) + 1 :]
                e = dict(it)
                e["field"] = trimmed
                out.append(e)
            else:
                out.append(it)
        return out

    def _group_spatiotemporal(items, cat_name):
        """Level 1: by the first token AFTER 'spatial.'/'temporal.'
        Level 2: as usual – separate the '<name>.<idx>.*' lists into nested
        sections.
        """

        stripped = _strip_cat_prefix(items, cat_name)

        first = group_index_only(stripped)

        nested_grouped = {}
        for gkey, gitems in first["grouped"].items():
            nested_grouped[gkey.capitalize()] = nest_sublist_groups(gitems)

        return {"flat": first["flat"], "grouped": nested_grouped}

    grouped_meta = {}
    for cat, items in main_categories.items():
        if cat == "spatial":
            grouped = _group_spatiotemporal(items, "spatial")
        elif cat == "temporal":
            grouped = _group_spatiotemporal(items, "temporal")
        elif cat == "source":
            first = group_index_only(items)
            nested_grouped = {
                k: nest_sublist_groups(v) for k, v in first["grouped"].items()
            }
            grouped = {"flat": first["flat"], "grouped": nested_grouped}
        elif cat == "license":
            first = group_index_only(items)
            nested_grouped = {
                k: nest_sublist_groups(v) for k, v in first["grouped"].items()
            }
            grouped = {"flat": first["flat"], "grouped": nested_grouped}
        else:
            # general (unchanged)
            grouped = group_index_only(items)

        grouped_meta[cat] = {"flat": grouped["flat"], "grouped": grouped["grouped"]}

    for k in ("general", "spatial", "temporal", "source", "license"):
        grouped_meta.setdefault(k, {"flat": [], "grouped": {}})

    return grouped_meta


def get_all_field_descriptions(json_schema, prefix=""):
    """
    Collects the field title, descriptions, examples, and badge information
    for each field of the oemetadata from the JSON schema and prepares them
    for further processing.

    Args:
        json_schema (dict): The JSON schema to extract field descriptions from.
        prefix (str, optional): The prefix for nested keys. Defaults to an
            empty string.

    Returns:
        dict: A dictionary containing field descriptions, examples, and other
            information.
    """

    field_descriptions = {}

    def extract_descriptions(properties, prefix=""):
        for field, value in properties.items():
            key = f"{prefix}.{field}" if prefix else field

            if any(
                attr in value
                for attr in ["description", "examples", "example", "badge", "title"]
            ):
                field_descriptions[key] = {}
                if "description" in value:
                    field_descriptions[key]["description"] = value["description"]
                # Prefer v2 "examples" (array) over v1 "example" (single value)
                if "examples" in value and value["examples"]:
                    # v2: first item of the examples array
                    field_descriptions[key]["example"] = value["examples"][0]
                elif "example" in value:
                    # v1 fallback
                    field_descriptions[key]["example"] = value["example"]
                if "badge" in value:
                    field_descriptions[key]["badge"] = value["badge"]
                if "title" in value:
                    field_descriptions[key]["title"] = value["title"]
            if "properties" in value:
                new_prefix = f"{prefix}.{field}" if prefix else field
                extract_descriptions(value["properties"], new_prefix)
            if "items" in value:
                new_prefix = f"{prefix}.{field}" if prefix else field
                if "properties" in value["items"]:
                    extract_descriptions(value["items"]["properties"], new_prefix)

    extract_descriptions(json_schema["properties"], prefix)
    return field_descriptions
