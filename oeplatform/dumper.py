"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import os
import tarfile
from subprocess import call

import sqlalchemy as sqla
from securitysettings import dbhost, dbname, dbpasswd, dbport, dbuser

datarepowc = ""
excluded_schemas = ["information_schema", "public", "topology", "reference"]


def connect():
    engine = _get_engine()
    return sqla.inspect(engine)


def _get_engine():
    engine = sqla.create_engine(
        "postgresql://{0}:{1}@{2}:{3}/{4}".format(
            dbuser, dbpasswd, dbhost, dbport, dbname
        )
    )
    return engine


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


insp = connect()
for schema in insp.get_schema_names():
    if schema not in excluded_schemas:
        if not os.path.exists(datarepowc + schema):
            os.mkdir(datarepowc + schema)
        for table in insp.get_table_names(schema=schema):
            if not table.startswith("_"):
                if not os.path.exists(datarepowc + schema + "/" + table):
                    os.mkdir(datarepowc + schema + "/" + table)
                L = [
                    "pg_dump",
                    "-h",
                    dbhost,
                    "-U",
                    dbuser,
                    "-d",
                    dbname,
                    "-F",
                    "d",
                    "-f",
                    datarepowc + schema + "/" + table,
                    "-t",
                    schema + "." + table,
                    "-w",
                ]
                call(L)
                L = [
                    "tar",
                    "-zcf",
                    datarepowc + schema + "/" + table + ".tar.gz",
                    "-C",
                    datarepowc + schema + "/",
                    table + "/",
                ]
                call(L)
                L = ["rm", "-r", datarepowc + schema + "/" + table]

                call(L)
