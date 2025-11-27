"""admin command to check for dead links in test environment

looking for
* static content (css, js, images)
* web pages
* javascript that opens local pages


start with `python management.py check_links http://localhost:8000 --no-external`

or whatever your test enviroment is.

Probably not useful on a productive server as it will iterate
over every table page as well.
This is by no means perfect, but covers a lot of possible broken links


SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
import urllib3
from bs4 import BeautifulSoup, Tag
from django.core.management.base import BaseCommand

cache = {}


def iter_links(url, parent_url=None, root_url=None, no_external=False):
    res = requests.get(
        url,
        stream=True,  # stream because sometimes we dont actually load all the content
        verify=False,  # sometimes ssl certs fail
        headers={"User-Agent": "Mozilla/5.0"},
    )
    cache[url] = res.status_code

    # check if page should be parsed
    root_url = (root_url or url).rstrip("/")
    parse = (
        res.ok
        and url.startswith(root_url)
        and "text/html" in res.headers.get("content-type", "").lower()  # not external
    )

    if not res.ok:
        print("%s %s (SOURCE: %s)", res.status_code, url, parent_url)

    if not parse:
        res.close()  # close stream
        return

    # load and parse page

    html = BeautifulSoup(res.content, "html.parser")

    def filter_tag(t: Tag) -> bool:
        return bool(t.get("src") or t.get("href") or t.get("onclick"))

    # find all tags with href or src attribute
    tag: Tag
    for tag in html.find_all(filter_tag):
        if tag.get("onclick"):
            ref = str(tag.get("onclick", ""))
            match = re.match(
                r'.*window.location[ ]*=[ ]*["\']([^"\']+)', ref
            ) or re.match(r'.*window.open[ ]*\([ ]*["\']([^"\']+)', ref)
            if match:
                ref = match.groups()[0]
            else:
                continue
        else:
            ref = str(tag.get("src") or tag.get("href") or "")

        if not ref:
            continue

        # create absolute url
        ref = urljoin(url, ref)

        is_external = not ref.startswith(root_url)
        if no_external and is_external:
            continue

        ref_parts = urlparse(ref)
        if ref_parts.scheme not in ("http", "https"):
            continue
        # remove query args and fragments for internals
        if not is_external:
            ref = urlunparse(ref_parts._replace(fragment="", query=""))

        if ref in cache:  # already processed
            continue
        # only parse local links that come from an <a> tag
        parse = ref.startswith(root_url) and tag.name == "a"
        iter_links(ref, root_url=root_url, parent_url=url, no_external=no_external)


class Command(BaseCommand):
    help = "check for dead links"

    def add_arguments(self, parser):
        parser.add_argument(
            "instance", help="url to running test instance (e.g. http://localhost:8000)"
        )
        parser.add_argument(
            "--no-external", action="store_true", help="skip external links"
        )

    def handle(self, *args, **options):
        # Suppress only the insecure request warning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        iter_links(options["instance"], no_external=options["no_external"])
