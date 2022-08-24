"""admin command to check for dead links in test environment

looking for
* static content (css, js, images)
* web pages
* javascript that opens local pages


start with `python management.py check_links http://localhost:8000 --no-external`

or whatever your test enviroment is.

Probably not useful on a productive server as it will iterate over every table page as well.
This is by no means perfect, but covers a lot of possible broken links

"""
import logging
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

cache = {}


def iter_links(url, parent_url=None, root_url=None, no_external=False):

    res = requests.get(
        url, stream=True
    )  # stream because sometimes we dont actually load all the content
    cache[url] = res.status_code

    # check if page should be parsed
    root_url = (root_url or url).rstrip("/")
    parse = (
        res.ok
        and url.startswith(root_url)
        and "text/html" in res.headers.get("content-type", "").lower()  # not external
    )

    if not res.ok:
        logging.error("%s %s (SOURCE: %s)", res.status_code, url, parent_url)
    else:
        logging.info("%s %s (parse=%s)", res.status_code, url, parse)

    if not parse:
        res.close()  # close stream
        return

    # load and parse page

    html = BeautifulSoup(res.content, "html.parser")
    # find all tags with href or src attribute
    for t in html.find_all(lambda t: t.get("src") or t.get("href") or t.get("onclick")):
        if t.get("onclick"):
            ref = t.get("onclick")
            match = re.match(
                r'.*window.location[ ]*=[ ]*["\']([^"\']+)', ref
            ) or re.match(r'.*window.open[ ]*\([ ]*["\']([^"\']+)', ref)
            if match:
                ref = match.groups()[0]
            else:
                logging.debug("skipping %s", ref)
                continue
        else:
            ref = t.get("src") or t.get("href")

        if not ref:
            continue

        # create absolute url
        ref = urljoin(url, ref)

        if no_external and not ref.startswith(root_url):
            continue

        # remove query args and fragments
        ref = urlparse(ref)
        if ref.scheme not in ("http", "https"):
            continue
        ref = urlunparse(ref._replace(fragment="", query=""))
        if ref in cache:  # already processed
            continue
        # only parse local links that come from an <a> tag
        parse = ref.startswith(root_url) and t.name == "a"
        iter_links(ref, root_url=root_url, parent_url=url, no_external=no_external)


class Command(BaseCommand):
    help = "check for dead links"

    def add_arguments(self, parser):
        parser.add_argument(
            "instance", help="url to running test instance (e.g. http://localhost:8000)"
        )
        parser.add_argument(
            "--show-all", action="store_true", help="show all urls, not just dead links"
        )
        parser.add_argument(
            "--no-external", action="store_true", help="only check local links"
        )

    def handle(self, *args, **options):

        loglevel = logging.INFO if options["show_all"] else logging.WARNING

        logging.basicConfig(
            format="[%(asctime)s %(levelname)7s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=loglevel,
        )

        iter_links(options["instance"], no_external=options["no_external"])
