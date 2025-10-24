"""
Provide helper functionality for views to reduce code lines in views.py
make the codebase more modular.

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Daryna Barabanova <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from wsgiref.util import FileWrapper

from django.contrib.postgres.search import SearchQuery
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.encoding import smart_str

import api.parser
from api import actions
from dataedit.models import PeerReview, Table, Tag
from oeplatform.settings import MEDIA_ROOT

# TODO: WINGECHR: model_draft is not a topic, but currently,
# frontend still usses it to filter / search for unpublished data
TODO_PSEUDO_TOPIC_DRAFT = "model_draft"


##############################################
#       Open Peer Review related             #
##############################################


def merge_field_reviews(current_json, new_json):
    """
    Merge reviews from contributors and reviewers into a single JSON object.

    Args:
        current_json (dict): The current JSON object containing
            reviewer's reviews.
        new_json (dict): The new JSON object containing contributor's reviews.

    Returns:
        dict: The merged JSON object containing both contributor's and
            reviewer's reviews.

    Note:
        If the same key is present in both the contributor's and
            reviewer's reviews, the function will merge the field
            evaluations. Otherwise, it will create a new entry in
            the Review-Dict.
    """
    merged_json = new_json.copy()
    review_dict = {}

    for contrib_review in merged_json["reviews"]:
        category = contrib_review["category"]
        key = contrib_review["key"]
        review_dict[(category, key)] = contrib_review["fieldReview"]

    for reviewer_review in current_json["reviews"]:
        category = reviewer_review["category"]
        key = reviewer_review["key"]

        if (category, key) in review_dict:
            # Add field evaluations to the existing entry
            existing_field_review = review_dict[(category, key)]
            if isinstance(existing_field_review, dict):
                existing_field_review = [existing_field_review]
            if isinstance(reviewer_review["fieldReview"], dict):
                reviewer_review["fieldReview"] = [reviewer_review["fieldReview"]]
            merged_field_review = existing_field_review + reviewer_review["fieldReview"]
            review_dict[(category, key)] = merged_field_review
        else:
            # Create new entry in Review-Dict
            review_dict[(category, key)] = reviewer_review["fieldReview"]

    # Insert updated field scores back into the JSON
    merged_json["reviews"] = [
        {"category": category, "key": key, "fieldReview": review_dict[(category, key)]}
        for category, key in review_dict
    ]

    return merged_json


def get_review_for_key(key, review_data):
    """
    Retrieve the review for a specific key from the review data.

    Args:
        key (str): The key for which to retrieve the review.
            review_data (dict): The review data containing
            reviews for various keys.

    Returns:
        Any: The new value associated with the specified key
            in the review data, or None if the key is not found.
    """

    for review in review_data["reviewData"]["reviews"]:
        if review["key"] == key:
            return review["fieldReview"].get("newValue", None)
    return None


def recursive_update(metadata, review_data):
    """
    Recursively updates metadata with new values from review_data,
    skipping or removing fields with status 'rejected'.

    Args:
    metadata (dict): The original metadata dictionary to update.
    review_data (dict): The review data containing the new values
    for various keys.

    Note:
    The function iterates through the review data and for each key
    updates the corresponding value in metadata if the new value is
    present and is not an empty string, and if the field status is
    not 'rejected'.
    """

    def delete_nested_field(data, keys):
        """
        Removes a nested field from a dictionary based on a list of keys.

        Args:
            data (dict or list): The dictionary or list from which
            to remove the field.
            keys (list): A list of keys pointing to the field to remove.
        """
        for key in keys[:-1]:
            if isinstance(data, list):
                key = int(key)
            data = data.get(key) if isinstance(data, dict) else data[key]

        last_key = keys[-1]
        if isinstance(data, list) and last_key.isdigit():
            index = int(last_key)
            if 0 <= index < len(data):
                data.pop(index)
        elif isinstance(data, dict):
            data.pop(last_key, None)

    for review_key in review_data["reviewData"]["reviews"]:
        keys = review_key["key"].split(".")

        field_review = review_key.get("fieldReview")
        if isinstance(field_review, list):
            field_rejected = False
            for fr in field_review:
                state = fr.get("state")
                if state == "rejected":
                    # If a field is rejected, delete it and move on to the next one.
                    delete_nested_field(metadata, keys)
                    field_rejected = True
                    break
            if field_rejected:
                continue

            # If the field is not rejected, apply the new value
            for fr in field_review:
                new_value = fr.get("newValue", None)
                if new_value is not None and new_value != "":
                    set_nested_value(metadata, keys, new_value)

        elif isinstance(field_review, dict):
            state = field_review.get("state")
            if state == "rejected":
                # If a field is rejected, delete it and move on to the next one.
                delete_nested_field(metadata, keys)
                continue

            # If the field is not rejected, apply the new value
            new_value = field_review.get("newValue", None)
            if new_value is not None and new_value != "":
                set_nested_value(metadata, keys, new_value)

    return metadata


def set_nested_value(metadata, keys, value):
    """
    Set a nested value in a dictionary given a sequence of keys.

    Args:
        metadata (dict): The dictionary in which to set the value.
        keys (list): A list of keys representing the path to the nested value.
        value (Any): The value to set.

    Note:
        The function navigates through the dictionary using the keys
        and sets the value at the position indicated by the last key in the list.
    """

    for key in keys[:-1]:
        if key.isdigit():
            key = int(key)
        metadata = metadata[key]
    last_key = keys[-1]
    if last_key.isdigit():
        last_key = int(last_key)
    metadata[last_key] = value


def process_review_data(review_data, metadata, categories):
    state_dict = {}

    # Initialize fields
    for category in categories:
        for item in metadata[category]:
            item["reviewer_suggestion"] = ""
            item["suggestion_comment"] = ""
            item["additional_comment"] = ""
            item["newValue"] = ""

    for review in review_data:
        field_key = review.get("key")
        field_review = review.get("fieldReview")
        category = review.get("category")  # Get the category from the review

        if isinstance(field_review, list):
            # Sort and get the latest field review
            sorted_field_review = sorted(
                field_review, key=lambda x: x.get("timestamp"), reverse=True
            )
            latest_field_review = (
                sorted_field_review[0] if sorted_field_review else None
            )

            if latest_field_review:
                state = latest_field_review.get("state")
                reviewer_suggestion = latest_field_review.get("reviewerSuggestion")
                reviewer_suggestion_comment = latest_field_review.get("comment")
                newValue = latest_field_review.get("newValue")
                additional_comment = latest_field_review.get("additionalComment")
            else:
                state = None
                reviewer_suggestion = ""
                reviewer_suggestion_comment = ""
                newValue = ""
                additional_comment = ""
        else:
            state = field_review.get("state")
            reviewer_suggestion = field_review.get("reviewerSuggestion")
            reviewer_suggestion_comment = field_review.get("comment")
            newValue = field_review.get("newValue")
            additional_comment = field_review.get("additionalComment")

        # Update the item in the correct category
        if category in metadata:
            for item in metadata[category]:
                if item["field"] == field_key:
                    item["reviewer_suggestion"] = reviewer_suggestion or ""
                    item["suggestion_comment"] = reviewer_suggestion_comment or ""
                    item["additional_comment"] = additional_comment or ""
                    item["newValue"] = newValue or ""
                    break

        state_dict[field_key] = state

    return state_dict


def delete_peer_review(review_id):
    """
    Remove Peer Review by review_id.
    Args:
        review_id (int): ID review.

    Returns:
        JsonResponse: JSON response about successful deletion or error.
    """
    if review_id:
        peer_review = PeerReview.objects.filter(id=review_id).first()
        if peer_review:
            peer_review.delete()
            return JsonResponse({"message": "PeerReview successfully deleted."})
        else:
            return JsonResponse({"error": "PeerReview not found."}, status=404)
    else:
        return JsonResponse({"error": "Review ID is required."}, status=400)


##############################################
#          Views related                     #
##############################################


def get_popular_tags(
    schema_name: str | None = None, table_name: str | None = None, limit=10
):
    tags = get_all_tags(table_name=table_name)
    sort_tags_by_popularity(tags)

    return tags[:limit]


def get_all_tags(
    schema_name: str | None = None, table_name: str | None = None
) -> QuerySet[Tag]:
    """
    Load all tags of a specific table
    :param schema: Name of a schema
    :param table: Name of a table
    :return:
    """
    if table_name:
        tags = Table.objects.get(name=table_name).tags.all()
    else:
        tags = Tag.objects.all()

    return tags


def sort_tags_by_popularity(tags: QuerySet[Tag]) -> QuerySet[Tag]:
    return tags.order_by("-usage_count")


def change_requests(schema, table):
    """
    Loads the dataedit admin interface
    :param request:
    :return:
    """
    # I want to display old and new data, if different.

    display_message = None
    api_columns = actions.get_column_changes(reviewed=False, schema=schema, table=table)
    api_constraints = actions.get_constraints_changes(
        reviewed=False, schema=schema, table=table
    )

    data = dict()

    data["api_columns"] = {}
    data["api_constraints"] = {}

    keyword_whitelist = [
        "column_name",
        "c_table",
        "c_schema",
        "reviewed",
        "changed",
        "id",
    ]

    old_description = actions.describe_columns(schema, table)

    for change in api_columns:
        name = change["column_name"]
        id = change["id"]

        # Identifing over 'new'.
        if change.get("new_name") is not None:
            change["column_name"] = change["new_name"]

        old_cd = old_description.get(name)

        data["api_columns"][id] = {}
        data["api_columns"][id]["old"] = {}

        if old_cd is not None:
            old = api.parser.parse_scolumnd_from_columnd(
                schema, table, name, old_description.get(name)
            )

            for key in list(change):
                value = change[key]
                if key not in keyword_whitelist and (
                    value is None or value == old[key]
                ):
                    old.pop(key)
                    change.pop(key)
            data["api_columns"][id]["old"] = old
        else:
            data["api_columns"][id]["old"]["c_schema"] = schema
            data["api_columns"][id]["old"]["c_table"] = table
            data["api_columns"][id]["old"]["column_name"] = name

        data["api_columns"][id]["new"] = change

    for i in range(len(api_constraints)):
        value = api_constraints[i]
        id = value.get("id")
        if (
            value.get("reference_table") is None
            or value.get("reference_column") is None
        ):
            value.pop("reference_table")
            value.pop("reference_column")

        data["api_constraints"][id] = value

    display_style = [
        "c_schema",
        "c_table",
        "column_name",
        "not_null",
        "data_type",
        "reference_table",
        "constraint_parameter",
        "reference_column",
        "action",
        "constraint_type",
        "constraint_name",
    ]

    return {
        "data": data,
        "display_items": display_style,
        "display_message": display_message,
    }


def find_tables(
    topic_name: str | None = None,
    query_string: str | None = None,
    tag_ids: list[str] | None = None,
) -> QuerySet[Table]:
    """find tables given search criteria

    Args:
        topic_name (str, optional): only tables in this topic
        query_string (str, optional): user search term
        tag_ids (list, optional): list of tag ids

    Returns:
        QuerySet of Table objetcs
    """

    tables = Table.objects

    tables = tables.filter(is_sandbox=False)

    if topic_name:
        # TODO: WINGECHR: model_draft is not a topic, but currently,
        # frontend still usses it to filter / search for unpublished data
        if topic_name == TODO_PSEUDO_TOPIC_DRAFT:
            tables = tables.filter(is_publish=False)
        else:
            tables = tables.filter(topics__pk=topic_name)

    if query_string:  # filter by search terms
        tables = tables.filter(
            Q(
                search=SearchQuery(
                    " & ".join(p + ":*" for p in re.findall(r"[\w]+", query_string)),
                    search_type="raw",
                )
            )
        )

    if tag_ids:  # filter by tags:
        # find tables (in schema), that use all of the tags
        # by adding a filter for each tag
        # (instead of all at once, which would be OR)
        for tag_id in tag_ids:
            tables = tables.filter(tags__pk=tag_id)

    return tables


def _type_json(json_obj):
    """
    Recursively labels JSON-objects by their types. Singleton lists are handled
    as elementary objects.

    :param json_obj: An JSON-object - possibly a dictionary, a list
        or an elementary JSON-object (e.g a string)

    :return: An annotated JSON-object (type, object)

    """
    if isinstance(json_obj, dict):
        return "dict", [(k, _type_json(json_obj[k])) for k in json_obj]
    elif isinstance(json_obj, list):
        if len(json_obj) == 1:
            return _type_json(json_obj[0])
        return "list", [_type_json(e) for e in json_obj]
    else:
        return str(type(json_obj)), json_obj


def edit_tag(id: str, name: str, color: str) -> None:
    """
    Args:
        id(int): tag id
        name(str): max 40 character tag text
        color(str): hexadecimal color code, eg #aaf0f0
    Raises:
        sqlalchemy.exc.IntegrityError if name is not ok

    """
    tag = Tag.objects.get(pk=id)
    tag.name = name
    tag.color = Tag.color_from_hex(color)
    tag.save()


def delete_tag(id: str) -> None:
    Tag.objects.get(pk=id).delete()


def add_tag(name: str, color: str) -> None:
    """
    Args:
        name(str): max 40 character tag text
        color(str): hexadecimal color code, eg #aaf0f0
    """
    Tag(name=name, color=Tag.color_from_hex(color)).save()


def send_dump(schema, table, fname):
    path = MEDIA_ROOT + "/dumps/{schema}/{table}/{fname}.dump".format(
        fname=fname, schema=schema, table=table
    )
    f = FileWrapper(open(path, "rb"))
    response = HttpResponse(f, content_type="application/x-gzip")

    response["Content-Disposition"] = "attachment; filename=%s" % smart_str(
        "{schema}_{table}_{date}.tar.gz".format(date=fname, schema=schema, table=table)
    )

    # It's usually a good idea to set the 'Content-Length' header too.
    # You can also set any other required headers: Cache-Control, etc.
    return response


def update_keywords_from_tags(table: Table, schema: str) -> None:
    """synchronize keywords in metadata with tags"""

    metadata = table.oemetadata or {"resources": [{}]}
    keywords = [tag.name_normalized for tag in table.tags.all()]
    metadata["resources"][0]["keywords"] = keywords

    actions.set_table_metadata(table=table.name, metadata=metadata)


def get_column_description(schema, table):
    """Return list of column descriptions:
    [{
       "name": str,
       "data_type": str,
       "is_nullable': bool,
       "is_pk": bool
    }]

    """

    def get_datatype_str(column_def):
        """get single string sql type definition.

        We want the data type definition to be a simple string, e.g. decimal(10, 6)
        or varchar(128), so we need to combine the various fields
        (type, numeric_precision, numeric_scale, ...)
        """
        # for reverse validation, see also api.parser.parse_type(dt_string)
        dt = column_def["data_type"].lower()
        precisions = None
        if dt.startswith("character"):
            if dt == "character varying":
                dt = "varchar"
            else:
                dt = "char"
            precisions = [column_def["character_maximum_length"]]
        elif dt.endswith(" without time zone"):  # this is the default
            dt = dt.replace(" without time zone", "")
        elif re.match("(numeric|decimal)", dt):
            precisions = [column_def["numeric_precision"], column_def["numeric_scale"]]
        elif dt == "interval":
            precisions = [column_def["interval_precision"]]
        elif re.match(".*int", dt) and re.match(
            "nextval", column_def.get("column_default") or ""
        ):
            # dt = dt.replace('int', 'serial')
            pass
        elif dt.startswith("double"):
            dt = "float"
        if precisions:  # remove None
            precisions = [x for x in precisions if x is not None]
        if precisions:
            dt += "(%s)" % ", ".join(str(x) for x in precisions)
        return dt

    def get_pk_fields(constraints):
        """Get the column names that make up the primary key
        from the constraints definitions.

        NOTE: Currently, the wizard to create tables only supports
            single fields primary keys (which is advisable anyways)
        """
        pk_fields = []
        for _name, constraint in constraints.items():
            if constraint.get("constraint_type") == "PRIMARY KEY":
                m = re.match(
                    r"PRIMARY KEY[ ]*\(([^)]+)", constraint.get("definition") or ""
                )
                if m:
                    # "f1, f2" -> ["f1", "f2"]
                    pk_fields = [x.strip() for x in m.groups()[0].split(",")]
        return pk_fields

    _columns = actions.describe_columns(schema, table)
    _constraints = actions.describe_constraints(schema, table)
    pk_fields = get_pk_fields(_constraints)
    # order by ordinal_position
    columns = []
    for name, col in sorted(
        _columns.items(), key=lambda kv: int(kv[1]["ordinal_position"])
    ):
        columns.append(
            {
                "name": name,
                "data_type": get_datatype_str(col),
                "is_nullable": col["is_nullable"],
                "is_pk": name in pk_fields,
                "unit": None,
                "description": None,
            }
        )
    return columns


def get_cancle_state(request):
    return request.META.get("HTTP_REFERER")


def get_page(request: HttpRequest) -> int:
    try:
        return int(request.GET.get("page", "1"))
    except Exception:
        return 1
