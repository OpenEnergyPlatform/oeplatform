from django.utils.safestring import mark_safe

LICENSE_KEY = 'license'
COLUMNS_KEY = 'fields'


class MetaDataWidget:
    """Html display of metadata JSON variable"""

    def __init__(self, json):
        self.json = json

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
                    html += f'<tr><th>{key.capitalize()}:</th> {self.__convert_to_html(value, level + 1, parent=key)}</tr>'
                elif level >= 1:
                    if LICENSE_KEY in key:
                        html += self.__format_license(value, level)
                    elif COLUMNS_KEY in key:
                        html += self.__format_columns(value, level)
                    else:
                        html += f'<li><b>{key.capitalize()}:</b> {self.__convert_to_html(value, level + 1, parent=key)}</li>'

            html += '' if level == 0 else '</ul>'

        elif isinstance(data, list):



            no_valid_item = True

            for item in data:
                name = None
                if isinstance(item, dict):
                    item = item.copy()
                    name = item.pop('name', None)
                    if name is None:
                        name = item.pop('title', None)
                    url = item.pop('url', '')
                    if url != '':
                        name = f'<a href="{url}">{name}</a>'
                if name is not None:
                    no_valid_item = False
                    html += f'<p class="metaproperty">{name}{self.__convert_to_html(item, level + 1, parent=parent)}</p>'

            if no_valid_item:
                html += f'<p class="metaproperty">There is no valid entry for this field</p>'

        elif isinstance(data, str):
            html += f'{data}'
        else:
            html += str(type(data))

        if level == 0:
            html += '</table>'
        elif level == 1:
            html += '</td>'

        return html

    def __format_license(self, value, level):
        return f'<li><b>License:</b> {self.__convert_to_html(value, level + 1)}</li>'

    def __format_columns(self, columns, level):
        html = '<p class="metaproperty">'
        for item in columns:
            item = item.copy()

            name = item.pop('name')
            unit = item.pop('unit', '')
            if unit != '':
                html += f'{name} ({unit})'
            else:
                html += f'{name}'

            descr = item.pop('description', '')
            if descr != '':
                html += f': {descr}'
        html += '</p>'
        return html

    def render(self):
        answer = mark_safe(self.__convert_to_html(data=self.json))
        return answer
