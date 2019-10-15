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
                            html += f'<tr><th>Columns</th> <td>{self.__format_columns(value)}</td></tr>'
                        else:
                            html += f'<tr><th>{self.camel_case_split(key)}</th> {self.__convert_to_html(value, level + 1, parent=key)}</tr>'
                elif level >= 1:
                    html += f'<li><b>{self.camel_case_split(key)}:</b> {self.__convert_to_html(value, level + 1, parent=key)}</li>'

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
                    html += f'<li>{self.__convert_to_html(item, level + 1, parent=parent)}</li>'
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
                            name = f'<a href="{url}">{name}</a>'
                        if name is not None and name != '':
                            no_valid_item = False
                            html += f'<p class="metaproperty">{name}{self.__convert_to_html(item, level + 1, parent=parent)}</p>'
                    else:
                        html += f'<p>Not implemented yet</p>'

            if no_valid_item:
                html += f'<p class="metaproperty">There is no valid entry for this field</p>'

        elif isinstance(data, str) and re.match(self.url_regex, data):
            html += f'<a href="{data}">{data}</a>'
        elif isinstance(data, str):
            html += f'{data}'
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
                html += f'{name} ({unit})'
            else:
                html += f'{name}'
            html += '</p>'
            descr = item.pop('description', '')
            if descr != '':
                html += f'{descr}'
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
                    html += f'{self.__convert_to_form(value, level + 1, parent=key)}'
                    html += '<hr>'
            html.rstrip('<hr>')
        elif level > 0:
            label = parent.split('_')[-1]
            print(label)
            label = self.format_index_numbers(label)
            print(label)
            # between the horizontal lines the item can be a string, a list of objects or a dict
            if isinstance(data, str):
                # simply an input field and a label within a div
                html = '<div class="form_group">'
                html += f'<label for="{parent}"> {label} </label>'
                html += f'<input class="form-control" id="{parent}" name="{parent}" type="text" value="{data}" />'
                html += '</div>'
            elif isinstance(data, dict):
                html = '<table style="width:100%">'
                html += f'<tr><td style="width:150px"><label>{label.capitalize()}</label></td></tr>'
                html += '<tr><td></td><td>'
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
                html += f'<tr><td style="width:150px"><label for="{parent}_container">{label.capitalize()}</label></td></tr>'
                html += '<tr><td>'
                html += f'<div id="{parent}_container">'

                # TODO remove this loop and execute the list_field.html from the meta_edit.html
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
                html += f'<a onclick="add_list_objects(\'{parent}\')">Add</a>'

                html += '</td></tr>'
                html += '</table>'

        return html

    # TODO remove this function once the solution with list_field.html is implemented
    def __container(self, item, parent, idx):
        """wraps a container"""
        html = f'<div class="metacontainer" id={parent}{idx}>'

        html += f'<div class="metacontainer-header"><a style="color:white" onclick="$(\'#{parent}{idx}\').remove();"><span class="glyphicon glyphicon-minus-sign"/></a></div>'
        html += f'<div class="metaformframe" id={parent}{idx}>'
        html += item
        html += '</div>'
        html += '</div>'
        return html

    def render_editmode(self):

        answer = mark_safe(self.__convert_to_form(data=self.json))
        return answer