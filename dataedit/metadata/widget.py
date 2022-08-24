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
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
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

                    else:
                        html += mark_safe("<p>Not implemented yet</p>")

            if no_valid_item:
                html += mark_safe(
                    '<p class="metaproperty">There is no valid entry for this field</p>'
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

    def __convert_to_form(self, data, level=0, parent=""):
        """Formats variables into html form for editing

        :param data: either a dict, a list or a string
        :param level: the level of indentation inside the JSON variable
        :param parent ????
        :return:
        """
        if level == 0:
            # separate each item with a horizontal line
            html = mark_safe("")
            for key, value in data.items():
                if key not in METADATA_HIDDEN_FIELDS:
                    html += self.__convert_to_form(value, level + 1, parent=key)
                    html += mark_safe("<hr>")
                else:
                    html += mark_safe('<div class="metahiddenfield">')
                    html += self.__convert_to_form(value, level + 1, parent=key)
                    html += mark_safe("</div>")
                    html += format_html("<label>{}</label>", key)
                    html += self.__convert_to_html(value, level + 1, parent=key)
                    html += mark_safe("<hr>")

            html.rstrip("<hr>")
        elif level > 0:
            label = parent.split("_")[-1]
            label = self.format_index_numbers(label)
            # between the horizontal lines the item can be a string, a list of objects or a dict
            if isinstance(data, str) and "No json format" in data:
                # simply an input field and a label within a div
                self.is_error = True
                html = mark_safe('<div class="form_group">')
                html += format_html(
                    '<label class="field-str-label" for="{}"> {} </label>',
                    parent,
                    label,
                )
                html += format_html(
                    '<input class="form-control" id="{}" name="{}" type="text" value="{}" />',
                    parent,
                    parent,
                    data,
                )
                html += mark_safe("</div>")
            elif isinstance(data, str) and self.is_error is True:
                self.is_error = False
                # simply an input field and a label within a div
                html = mark_safe('<div class="form_group">')
                html += format_html(
                    '<label class="field-str-label" for="{}"> {} </label>',
                    parent,
                    label,
                )
                html += format_html(
                    '<textarea class="form-control" id="{}" name="{}" type="text">"{}" </textarea>',
                    parent,
                    parent,
                    data,
                )
                html += mark_safe("</div>")
            elif isinstance(data, str):
                # simply an input field and a label within a div
                html = mark_safe('<div class="form_group">')
                html += format_html(
                    '<label class="field-str-label" for="{}"> {} </label>',
                    parent,
                    label,
                )
                html += format_html(
                    '<input class="form-control" id="{}" name="{}" type="text" value="{}" />',
                    parent,
                    parent,
                    data,
                )
                html += mark_safe("</div>")
            elif data is None:
                # if data has no tpye, add an input field and a label within a div
                html = mark_safe('<div class="form_group">')
                html += format_html(
                    '<label class="field-str-label" for="{}"> {} </label>',
                    parent,
                    label,
                )
                # None has to be written as null in JSON context
                html += format_html(
                    '<input class="form-control" id="{}" name="{}" type="text" value="null" />',
                    parent,
                    parent,
                )
                html += mark_safe("</div>")
            elif isinstance(data, dict):
                html = mark_safe('<table style="width:100%">')
                html += mark_safe('<tr><td style="width:150px">')
                html += format_html(
                    '<label class="field-dict-label">{}</label>', label.capitalize()
                )
                html += mark_safe("</td></tr>")
                html += mark_safe('<tr><td style="width:20px"></td><td>')
                for key, value in data.items():
                    html += self.__convert_to_form(
                        value, level + 1, parent="{}_{}".format(parent, key)
                    )

                html += mark_safe("</td></tr>")
                html += mark_safe("</table>")
            elif isinstance(data, list):
                html = mark_safe('<table style="width:100%">')
                html += mark_safe('<tr><td style="width:150px">')
                html += format_html(
                    '<label class="field-list-label for="{}_container">', parent
                )
                html += conditional_escape(label.capitalize())
                html += mark_safe("</label></td></tr>")
                html += mark_safe("<tr><td>")
                html += format_html('<div id="{}_container">', parent)

                for i, item in enumerate(data):
                    html += self.__container(
                        self.__convert_to_form(
                            item, level + 1, parent="{}{}".format(parent, i)
                        ),
                        parent,
                        i,
                    )
                html += mark_safe("</div>")

                # bind to js function defined in dataedit/static/dataedit/metadata.js
                # to add new elements to the list upon user click
                html += format_html(
                    "<a onclick=\"add_list_objects('{}')\">Add</a>", parent
                )

                html += mark_safe("</td></tr>")
                html += mark_safe("</table>")

        return html

    # TODO remove this function once the solution with list_field.html is implemented
    def __container(self, item, parent, idx):
        """wraps a container"""
        html = format_html('<div class="metacontainer" id="{}{}">', parent, idx)

        html += mark_safe('<div class="metacontainer-header">')
        html += format_html(
            '<a style="color:white" onclick="remove_element(\'{}{}\')">', parent, idx
        )
        html += mark_safe('<span class="fas fa-minus"/></a></div>')
        html += format_html('<div class="metaformframe" id="{}{}">', parent, idx)
        html += conditional_escape(item)
        html += mark_safe("</div>")
        html += mark_safe("</div>")
        return html

    def render_editmode(self):

        answer = self.__convert_to_form(data=self.json)
        return answer
