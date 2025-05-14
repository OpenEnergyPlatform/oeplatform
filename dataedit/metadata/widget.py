# SPDX-FileCopyrightText: 2025 Alexis Michaltsis <https://github.com/4lm>
# SPDX-FileCopyrightText: 2025 Pierre Francois <pierre-francois.duc@rl-institut.de>
# SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk>
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

import re

from django.utils.html import conditional_escape, format_html, format_html_join
from django.utils.safestring import mark_safe

from dataedit.metadata import METADATA_HIDDEN_FIELDS

LICENSE_KEY = "license"
COLUMNS_KEY = "fields"


class MetaDataWidget:
    """Html display of metadata JSON variable"""

    is_error = False

    def __init__(self, json):
        self.json = json
        self.url_regex = re.compile(
            r"^(?:http|ftp)s?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # noqa
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

    def camel_case_split(self, string):
        matches = re.finditer(
            ".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", string
        )
        matches = [m.group(0) for m in matches]
        matches[0] = matches[0].capitalize()
        return format_html_join("", "{}", ((m,) for m in matches))

    def format_index_numbers(self, string):
        """Remove numbers in string

        :param string:
        :return:
        """
        answer = string
        match = re.match(r"([a-z]+)([0-9]+)", string, re.I)
        if match:
            items = match.groups()
            answer = format_html("{} {}", *items)

        return self.camel_case_split(answer)

    def __convert_to_html(self, data, level=0, parent=""):
        """Formats variables into html code

        :param data: either a dict, a list or a string
        :param level: the level of indentation inside the JSON variable
        :return:
        """

        if level == 0:
            html = mark_safe('<table class="table table-responsive">')
        elif level == 1:
            html = mark_safe("<td>")
        else:
            html = mark_safe("")

        if isinstance(data, dict):
            html += mark_safe("") if level == 0 else mark_safe("<ul>")
            for key, value in data.items():
                if level == 0:
                    if key not in METADATA_HIDDEN_FIELDS:
                        if COLUMNS_KEY in key:
                            html += mark_safe("<tr><th>Columns</th> <td>")
                            html += self.__format_columns(value)
                            html += mark_safe("</td></tr>")
                        else:
                            html += mark_safe("<tr><th>")
                            html += self.camel_case_split(key)
                            html += mark_safe("</th>")
                            html += self.__convert_to_html(value, level + 1, parent=key)
                            html += mark_safe("</tr>")
                elif level >= 1:
                    html += mark_safe("<li><b>")
                    html += self.camel_case_split(key)
                    html += mark_safe(":</b> ")
                    html += self.__convert_to_html(value, level + 1, parent=key)
                    html += mark_safe("</li>")

            html += mark_safe("") if level == 0 else mark_safe("</ul>")

        elif isinstance(data, list):
            # For list item control
            no_valid_item = True

            # Check if the first item of the list is a string
            string_list = False
            if len(data) > 0:
                if isinstance(data[0], str):
                    string_list = True
                    no_valid_item = False

            if string_list:
                html += mark_safe("<ul>")
                for item in data:
                    html += mark_safe("<li>")
                    html += self.__convert_to_html(item, level + 1, parent=parent)
                    html += mark_safe("</li>")
                html += mark_safe("</ul>")

            else:
                for item in data:
                    if isinstance(item, dict):
                        item = item.copy()
                        name = item.get("title", None)
                        if name is None or name == "":
                            name = item.get("name", None)
                        else:
                            item.get("name", None)
                        url = item.get("url", "")
                        if url != "":
                            name = format_html('<a href="{}">{}</a>', url, name)
                        if name is not None and name != "":
                            no_valid_item = False
                            html += mark_safe('<p class="metaproperty">')
                            html += conditional_escape(name) + self.__convert_to_html(
                                item, level + 1, parent=parent
                            )
                            html += mark_safe("</p>")
                        if item.get("start", None) is not None:
                            no_valid_item = False
                            html += mark_safe("<br>")
                            html += mark_safe("{} element".format(parent))
                            html += self.__convert_to_html(
                                item, level + 1, parent=parent
                            )

                        if item.get("reference", None) is not None:
                            no_valid_item = False
                            html += mark_safe("<br>")
                            # html += mark_safe("{} element".format(parent))
                            html += self.__convert_to_html(
                                item, level + 1, parent=parent
                            )

                    else:
                        html += mark_safe("<p>Can't render this entry.</p>")

            if no_valid_item:
                html += mark_safe(
                    '<p class="metaproperty">The entry is empty or there is no valid '
                    "entry for this field.</p>"
                )

        elif isinstance(data, str) and re.match(self.url_regex, data):
            html += format_html('<a href="{}">{}</a>', data, data)
        elif isinstance(data, str):
            html += conditional_escape(data)
        elif data is None:
            html += mark_safe("-")
        else:
            html += conditional_escape(str(type(data)))

        if level == 0:
            html += mark_safe("</table>")
        elif level == 1:
            html += mark_safe("</td>")

        return html

    def __format_columns(self, columns):
        html = mark_safe("")
        for item in columns:
            html += mark_safe('<p class="metaproperty">')
            item = item.copy()

            name = item.get("name")
            unit = item.get("unit", "")
            if unit != "":
                html += format_html("{} ({})", name, unit)
            else:
                html += conditional_escape(str(name))
            html += mark_safe("</p>")
            descr = item.get("description", "")
            if descr != "":
                html += conditional_escape(str(descr))
            else:
                html += mark_safe("No description ")
            html += mark_safe("<hr>")
        return html

    def render(self):
        answer = self.__convert_to_html(data=self.json)
        return answer
