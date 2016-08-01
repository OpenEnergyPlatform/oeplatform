import oeplatform.securitysettings as sec
import sqlalchemy as sqla
from subprocess import call
import os

excluded_schemas = [

    "information_schema",
    "public",
    "topology",
    "reference",
]


def connect():
    engine = _get_engine()
    return sqla.inspect(engine)


def _get_engine():
    engine = sqla.create_engine(
        'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
            sec.dbuser,
            sec.dbpasswd,
            sec.dbhost,
            sec.dbport,
            sec.dbname))
    return engine


insp = connect()
for schema in insp.get_schema_names():
    if schema not in excluded_schemas:
        if not os.path.exists(sec.datarepowc + schema):
            os.mkdir(sec.datarepowc + schema)
        for table in insp.get_table_names(schema=schema):
            if not table.startswith('_'):
                if not os.path.exists(sec.datarepowc + schema + '/' + table):
                    os.mkdir(sec.datarepowc + schema + '/' + table)
                L = ['pg_dump', '-h', sec.dbhost, '-U', sec.dbuser, '-d',
                     sec.dbname, '-F', 'd', '-f',
                     sec.datarepowc + schema + '/' + table, '-t',
                     schema + '.' + table, '-w', ]
                print(L)
                call(L)
                call(['tar', '-zcf',
                      sec.datarepowc + schema + '/' + table + '.tar.gz',
                      sec.datarepowc + schema + '/' + table])
                call(['rm', '-r',
                      sec.datarepowc + schema + '/' + table])
