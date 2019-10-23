import re

from django.utils.safestring import mark_safe

from dataedit.metadata import METADATA_HIDDEN_FIELDS

LICENSE_KEY = 'license'
COLUMNS_KEY = 'fields'


class MetaDataWidget:
    """Html display of metadata JSON variable"""

    def __init__(self, json):
        self.json = json
        self.url_regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )

    def camel_case_split(self, string):
        matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', string)
        matches = [m.group(0) for m in matches]
        matches[0] = matches[0].capitalize()
        return " ".join(matches)

    def format_index_numbers(self, string):
        """Remove numbers in string

        :param string:
        :return:
        """
        answer = string
        match = re.match(r"([a-z]+)([0-9]+)", string, re.I)
        if match:
            items = match.groups()
            answer = '{} {}'.format(*items)

        return self.camel_case_split(answer)


    def __convert_to_html(self, data, level=0, parent=''):
        """Formats variables into html code

        :param data: either a dict, a list or a string
        :param level: the level of indentation inside the JSON variable
        :return:
        """

        if level == 0:
            html = '<table class="table">'
        elif level == 1:
            html = '<td>'
        else:
            html = ''

        if isinstance(data, dict):

            html += '' if level == 0 else '<ul>'
            for key, value in data.items():
                if level == 0:
                    if key not in METADATA_HIDDEN_FIELDS:
                        if COLUMNS_KEY in key:
                            html += '<tr><th>Columns</th> <td>'
                            html += self.__format_columns(value)
                            html += '</td></tr>'
                        else:
                            html += '<tr><th>'
                            html += self.camel_case_split(key)
                            html += '</th>'
                            html += self.__convert_to_html(value, level + 1, parent=key)
                            html += '</tr>'
                elif level >= 1:
                    html += '<li><b>'
                    html += self.camel_case_split(key)
                    html += ':</b> '
                    html += self.__convert_to_html(value, level + 1, parent=key)
                    html += '</li>'

            html += '' if level == 0 else '</ul>'

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
                html += '<ul>'
                for item in data:
                    html += '<li>'
                    html += self.__convert_to_html(item, level + 1, parent=parent)
                    html += '</li>'
                html += '</ul>'

            else:
                for item in data:
                    if isinstance(item, dict):
                        item = item.copy()
                        name = item.pop('title', None)
                        if name is None or name == '':
                            name = item.pop('name', None)
                        else:
                            item.pop('name', None)
                        url = item.pop('url', '')
                        if url != '':
                            name = '<a href="{}">{}</a>'.format(url, name)
                        if name is not None and name != '':
                            no_valid_item = False
                            html += '<p class="metaproperty">'
                            html += name + self.__convert_to_html(item, level + 1, parent=parent)
                            html += '</p>'
                    else:
                        html += '<p>Not implemented yet</p>'

            if no_valid_item:
                html += '<p class="metaproperty">There is no valid entry for this field</p>'

        elif isinstance(data, str) and re.match(self.url_regex, data):
            html += '<a href="{}">{}</a>'.format(data, data)
        elif isinstance(data, str):
            html += data
        else:
            html += str(type(data))

        if level == 0:
            html += '</table>'
        elif level == 1:
            html += '</td>'

        return html

    def __format_columns(self, columns):
        html = ''
        for item in columns:
            html += '<p class="metaproperty">'
            item = item.copy()

            name = item.pop('name')
            unit = item.pop('unit', '')
            if unit != '':
                html += '{} ({})'.format(name, unit)
            else:
                html += str(name)
            html += '</p>'
            descr = item.pop('description', '')
            if descr != '':
                html += str(descr)
            else:
                html += 'No description '
            html += '<hr>'
        return html

    def render(self):
        answer = mark_safe(self.__convert_to_html(data=self.json))
        return answer

    def __convert_to_form(self, data, level=0, parent=''):
        """Formats variables into html form for editing

        :param data: either a dict, a list or a string
        :param level: the level of indentation inside the JSON variable
        :return:
        """

        if level == 0:
            # separate each item with a horizontal line
            html = ''
            for key, value in data.items():
                if key not in METADATA_HIDDEN_FIELDS:
                    html += self.__convert_to_form(value, level + 1, parent=key)
                    html += '<hr>'
                else:
                    html += '<div class="metahiddenfield">'
                    html += self.__convert_to_form(value, level + 1, parent=key)
                    html += '</div>'
                    html += '<label>{}</label>'.format(key)
                    html += self.__convert_to_html(value, level + 1, parent=key)
                    html += '<hr>'

            html.rstrip('<hr>')
        elif level > 0:
            label = parent.split('_')[-1]
            label = self.format_index_numbers(label)
            # between the horizontal lines the item can be a string, a list of objects or a dict
            if isinstance(data, str):
                # simply an input field and a label within a div
                html = '<div class="form_group">'
                html += '<label class="field-str-label" for="{}"> {} </label>'.format(
                    parent,
                    label
                )
                html += '<input class="form-control" id="{}" name="{}" type="text" value="{}" />'.format(parent, parent, data)
                html += '</div>'
            elif data is None:
                # if data has no tpye, add an input field and a label within a div
                html = '<div class="form_group">'
                html += '<label class="field-str-label" for="{}"> {} </label>'.format(
                    parent,
                    label
                )
                # None has to be written as null in JSON context
                html += '<input class="form-control" id="{}" name="{}" type="text" value="null" />'.format(parent, parent)
                html += '</div>'
            elif isinstance(data, dict):
                html = '<table style="width:100%">'
                html += '<tr><td style="width:150px">'
                html += '<label class="field-dict-label">{}</label>'.format(label.capitalize())
                html += '</td></tr>'
                html += '<tr><td style="width:20px"></td><td>'
                for key, value in data.items():
                    html += self.__convert_to_form(
                        value,
                        level + 1,
                        parent='{}_{}'.format(parent, key)
                    )

                html += '</td></tr>'
                html += '</table>'
            elif isinstance(data, list):
                html = '<table style="width:100%">'
                html += '<tr><td style="width:150px">'
                html += '<label class="field-list-label for="{}_container">'.format(parent)
                html += label.capitalize()
                html += '</label></td></tr>'
                html += '<tr><td>'
                html += '<div id="{}_container">'.format(parent)

                for i, item in enumerate(data):
                    html += self.__container(
                        self.__convert_to_form(
                            item,
                            level + 1,
                            parent='{}{}'.format(parent, i)
                        ),
                        parent,
                        i
                    )
                html += '</div>'

                # bind to js function defined in dataedit/static/dataedit/metadata.js
                # to add new elements to the list upon user click
                html += '<a onclick="add_list_objects(\'{}\')">Add</a>'.format(parent)

                html += '</td></tr>'
                html += '</table>'

        return html

    # TODO remove this function once the solution with list_field.html is implemented
    def __container(self, item, parent, idx):
        """wraps a container"""
        html = '<div class="metacontainer" id="{}{}">'.format(parent, idx)

        html += '<div class="metacontainer-header">'
        html += '<a style="color:white" onclick="remove_element(\'{}{}\')">'.format(parent, idx)
        html += '<span class="glyphicon glyphicon-minus-sign"/></a></div>'
        html += '<div class="metaformframe" id="{}{}">'.format(parent, idx)
        html += item
        html += '</div>'
        html += '</div>'
        return html

    def render_editmode(self):

        answer = mark_safe(self.__convert_to_form(data=self.json))
        return answer
