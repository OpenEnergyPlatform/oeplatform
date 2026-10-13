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


CHANGELOG_DIR = os.path.join(SITE_ROOT, "..", "versions", "changelogs")
RELEASED_CHANGELOG = re.compile(r"(\d+)_(\d+)_(\d+)\.md")
HIGHLIGHTS = re.compile(r"^## Highlights[ \t]*\n(.*?)(?=^## |\Z)", re.M | re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)


@lru_cache(maxsize=None)
def latest_release_highlights(directory=CHANGELOG_DIR) -> str:
    """HTML of the newest released changelog's `## Highlights`, or "".

    A released changelog is named `<major>_<minor>_<patch>.md` (`current.md` is
    the next release, not yet out). A release without highlights, as a patch
    release usually is, is skipped. The version is deliberately not returned:
    the platform's pages do not say which release it runs. Cached for the
    process: changelogs only change with a release, which restarts it.
    """
    released = []
    for name in os.listdir(directory):
        match = RELEASED_CHANGELOG.fullmatch(name)
        if match:
            released.append((tuple(int(part) for part in match.groups()), name))
    for _version, name in sorted(released, reverse=True):
        with open(os.path.join(directory, name), encoding="utf-8") as file:
            section = HIGHLIGHTS.search(file.read())
        text = COMMENT.sub("", section.group(1)).strip() if section else ""
        if text:
            return markdown2.markdown(text)
    return ""


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
        object: single json python object, None if no json carries that id
    """

    if path is not None:
        all_jsons = []
        for _json in os.listdir(path=path):
            # only the project pages: the directory is bind-mounted in the docker
            # dev setup and can hold other files, such as macOS' .DS_Store
            if not _json.endswith(".json"):
                continue
            with open(os.path.join(path, _json), "r", encoding="utf-8") as json_content:
                content = json.load(json_content)
                all_jsons.append(content)

        if json_id is None:
            return all_jsons
        else:
            return next(
                (i for i in all_jsons if json_id == i["id"] and "template" != i["id"]),
                None,
            )
    # TODO: catch the exception if path is none
    else:
        return {
            "error": "Path cant be None. Please provide the path to '/static/project_detail_pages_content/' . You can create a new Project by adding an JSON file like the '/static/project_detail_pages_content/PROJECT_TEMPLATE.json'."  # noqa
        }
