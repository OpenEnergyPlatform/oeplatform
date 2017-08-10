from api import actions

from dataedit.metadata import v1_3 as __LATEST


def load_comment_from_db(schema, table):
    comment = actions.get_comment_table(schema, table)
    if not comment:
        return __LATEST.get_empty(schema, table)

    if 'metadata_version' in comment:
        version = __parse_version(comment['metadata_version'])
    else:
        version = min(
            __parse_version(x['meta_version']) for x in comment['resources'] if
            'meta_version' in x)
    if version[0] == 1:
        if version[1] == 1:
            return __LATEST.from_v1_1(comment, schema, table)
        elif version[1] == 2:
            return __LATEST.from_v1_2(comment)
        elif version[1] == 3:
            return comment
        else:
            return comment
    else:
        return __LATEST.from_v0(comment, schema, table)


def load_meta(c):
    d = {
        'title': c['title'],
        'description': c['description'],
        'reference_date': c['reference_date'],
        'spatial':{
            'location': c['spatial_location'],
            'extent': c['spatial_extend'],
            'resolution': c['spatial_resolution']
        },
        'temporal': {
            'reference_date': c['temporal_reference_date'],
            'start': c['temporal_start'],
            'end': c['temporal_end'],
            'resolution': c['temporal_resolution']
        },
        'license': {
            'id': c['license_id'],
            'name': c['license_name'],
            'version': c['license_version'],
            'url': c['license_url'],
            'instruction': c['license_instruction'],
            'copyright': c['license_copyright'],
        },
    }


    for prefix, f, props in [('language', load_language,1),('sources', load_sources,5), ('contributors', load_contributors,4), ('field', load_field, 3)]:
        count = len([(k,c[k]) for k in c if k.startswith(prefix)])//props
        d[prefix] = [f({k[len('%s%d'%(prefix,i+1))+1:]:c[k] for k in c if k.startswith('%s%d'%(prefix,i+1))}) for i in range(count)]

    d['resources'] = [
        {
            'name': c['resources_name'],
            'format': 'PostgreSQL',
            'fields':d['field']
        }
    ]
    d['metadata_version'] = '1.3'
    del d['field']

    return d


def load_sources(x):
    return {'name': x['name'], 'description': x['description'], 'url': x['url'],
            'license': x['license'], 'copyright': x['copyright']}


def load_language(x):
    # This looks weird, but makes things way more convenient
    # all other 'load'-functions expect dictionaries but languages do not have
    # labels. Thus, for the sake of convenience, an empty label is generated.
    return x['']


def load_contributors(x):
    return x


def load_field(x):
    return {'name': x['name'],
            'description': x['description'],
            'unit': x['unit']}

def load_metaversion(x):
    return x['']

def __parse_version(version_string):
    return tuple(map(int, version_string.split('.')))
