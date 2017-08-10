from api import actions
from . import v1_2


def from_v1_2(comment_on_table):
    if comment_on_table.get('spatial', False):
        comment_on_table['spatial'] = comment_on_table['spatial'][0]
    else:
         comment_on_table['spatial'] = {
            "location": '',
            "extent": '',
            "resolution": ''
         },

    comment_on_table['temporal'] = {
        "reference_date": comment_on_table['reference_date'],
        "start": '',
        "end": '',
        "resolution": ''
    }

    if comment_on_table.get('license', False):
        comment_on_table['license'] = comment_on_table['license'][0]
    else:
        comment_on_table['license'] = {
            "id": "",
            "name": "",
            "version": "",
            "url": "",
            "instruction": "",
            "copyright": ""
        }

    for i in range(len(comment_on_table['resources'])):
        comment_on_table['resources'][i] = {
            "name": "",
            "format": "PostgreSQL",
            "fields": comment_on_table['resources'][i]['schema']['fields']
        }

    comment_on_table['metadata_version'] = '1.3'

    return comment_on_table


def from_v1_1(comment_on_table, schema, table):
    return from_v1_2(v1_2.from_v1_1(comment_on_table, schema, table))


def from_v0(comment_on_table, schema, table):
    return from_v1_2(v1_2.from_v0(comment_on_table, schema, table))


def get_empty(schema, table):
    columns = actions.analyze_columns(schema, table)
    comment_on_table = {
            'title': '',
            'description': '',
            'language': ['eng'],
            'spatial':
                {'location': '',
                 'extent': '',
                 'resolution': ''},
            'temporal':
                {'reference_date': '',
                 'start': '',
                 'end': '',
                 'resolution': ''},
            'sources': [
                {'name': '', 'description': '', 'url': '', 'license': '',
                 'copyright': ''}
            ],
            'license':
                {'id': '',
                 'name': '',
                 'version': '',
                 'url': '',
                 'instruction': '',
                 'copyright': ''},
            'contributors': [
            ],
            'resources': [
                {
                    'name': '',
                    'format': 'PostgreSQL',
                    'fields': [{
                        'name': col['id'],
                        'description': '',
                        'unit': ''} for col in columns
                    ]
                }
            ],
            'metadata_version': '1.3'}
    return comment_on_table