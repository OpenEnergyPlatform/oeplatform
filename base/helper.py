"""
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 NB-KREDER\\kreder <https://github.com/klarareder> © Fraunhofer IEE
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import json
import logging
import os
import re
from functools import lru_cache

import markdown2

logger = logging.getLogger("oeplatform")
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))


@lru_cache(maxsize=None)
def read_version_changes() -> dict:
    """read version and changes from changelog markdown

    We use cache so it can stay in process memory and we dont have to read files
    in every request. this only changes on a new release anyway, in which case
    the process is restarted.

    Returns:
       dict: {"version": (major, minor, patch), "changes": changes}
    """
    os.path.dirname(os.path.realpath(__file__))
    version_expr = r"^(?P<major>\d+)\.(?P<minor>\d+)+\.(?P<patch>\d+)$"
    markdowner = markdown2.Markdown()

    logger.info("READING VERSION file.")
    try:
        with open(
            os.path.join(SITE_ROOT, "..", "VERSION"), encoding="utf-8"
        ) as version_file:
            match = re.match(version_expr, version_file.read())
            major, minor, patch = match.groups()
        with open(
            os.path.join(
                SITE_ROOT,
                "..",
                "versions/changelogs/%s_%s_%s.md" % (major, minor, patch),
            ),
            encoding="utf-8",
        ) as change_file:
            changes = markdowner.convert(
                "\n".join(line for line in change_file.readlines())
            )
    except Exception:
        logger.error("READING VERSION file.")
        # probably because change_file is missing
        major, minor, patch, changes = "", "", "", ""
    return {"version": (major, minor, patch), "changes": changes}


def get_json_content(path, json_id=None):
    """Parse all jsons from given path and return as
        list or return a single parsed json by id ->
        The json must have a field called id.

    Args:
        path (string): path to directory like 'static/project_pages_content/'
        json_id (string, optional): ID value that must match the value of json[id].
            Defaults to None.

    Returns:
        list[object]: List of all deserialized json files in path
        or
        object: single json python object
    """

    if path is not None:
        all_jsons = []
        for _json in os.listdir(path=path):
            with open(os.path.join(path, _json), "r", encoding="utf-8") as json_content:
                content = json.load(json_content)
                all_jsons.append(content)

        if json_id is None:
            return all_jsons
        else:
            content_by_id = [
                i for i in all_jsons if json_id == i["id"] and "template" != i["id"]
            ]
            return content_by_id[0]
    # TODO: catch the exception if path is none
    else:
        return {
            "error": "Path cant be None. Please provide the path to '/static/project_detail_pages_content/' . You can create a new Project by adding an JSON file like the '/static/project_detail_pages_content/PROJECT_TEMPLATE.json'."  # noqa
        }
