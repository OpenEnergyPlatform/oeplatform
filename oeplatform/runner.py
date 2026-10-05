"""
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later

The test runner (``TEST_RUNNER``): Django's, plus the data database (OEDB) the
run uses (see ``oeplatform/oedb_for_tests.py``).

Before Django creates its test database, ``prepare_test_oedb`` makes sure the
test OEDB exists, carries the extensions the migrations need, and is at
alembic's head revision. The database is kept after the run, like Django's
``--keepdb``: it holds only what tests leave behind, and the next run then
needs no migration. Drop it by hand to start from scratch.

Alembic runs in a subprocess, not in this process: ``oedb/env.py`` calls
``logging.config.fileConfig``, which disables every logger that exists
already, and so would silently break every test that uses ``assertLogs``.
"""  # noqa: 501

import os
import subprocess
import sys

import psycopg2
from django.core.exceptions import ImproperlyConfigured
from django.test.runner import DiscoverRunner
from psycopg2 import sql

from oeplatform import settings
from oeplatform.oedb_for_tests import FOR_TESTS_VARIABLE, TEST_NAME_VARIABLE

# What the OEDB's migrations need and the oeplatform-postgres image provides
# in its own databases.
EXTENSIONS = ("postgis", "postgis_topology", "hstore", "pg_trgm")


def _connect(name):
    connection = psycopg2.connect(
        dbname=name,
        user=settings.dbuser,
        password=settings.dbpasswd,
        host=settings.dbhost,
        port=settings.dbport,
    )
    connection.autocommit = True
    return connection


def _alembic_config():
    from alembic.config import Config

    config = Config(os.path.join(settings.BASE_DIR, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(settings.BASE_DIR, "oedb"))
    return config


def _head_revision() -> str:
    """Alembic's head, read off the migration files without running
    ``oedb/env.py``."""
    from alembic.script import ScriptDirectory

    return ScriptDirectory.from_config(_alembic_config()).get_current_head()


def _current_revision(cursor):
    cursor.execute("SELECT to_regclass('public.alembic_version')")
    if cursor.fetchone()[0] is None:
        return None
    cursor.execute("SELECT version_num FROM alembic_version")
    row = cursor.fetchone()
    return row[0] if row else None


def _create_if_missing(name):
    maintenance = _connect("postgres")
    try:
        with maintenance.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [name])
            if cursor.fetchone() is None:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name))
                )
    finally:
        maintenance.close()


def _extend(name):
    """Add the extensions; return the database's alembic revision."""
    test_oedb = _connect(name)
    try:
        with test_oedb.cursor() as cursor:
            for extension in EXTENSIONS:
                cursor.execute(
                    sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
                        sql.Identifier(extension)
                    )
                )
            return _current_revision(cursor)
    finally:
        test_oedb.close()


def prepare_test_oedb(name: str) -> None:
    """Create, extend and migrate the test OEDB ``name`` as needed.

    Refuses the configured OEDB outright: a test run must never write to it.
    """
    if name == settings.OEDB_CONFIGURED_NAME:
        raise ImproperlyConfigured(
            f"The test run would use the configured data database '{name}'. "
            f"Set {TEST_NAME_VARIABLE} to another name."
        )

    try:
        _create_if_missing(name)
        current = _extend(name)
    except psycopg2.Error as error:
        raise ImproperlyConfigured(
            f"Could not prepare the test data database '{name}': "
            f"{str(error).strip()}\nThe database user needs to be allowed to "
            "create databases and extensions. Otherwise create the database "
            f"yourself, with the extensions {', '.join(EXTENSIONS)}, and name "
            f"it in {TEST_NAME_VARIABLE}."
        ) from error

    if current == _head_revision():
        return
    environment = dict(
        os.environ, **{FOR_TESTS_VARIABLE: "1", TEST_NAME_VARIABLE: name}
    )
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=settings.BASE_DIR,
        env=environment,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Migrating the test data database '{name}' failed:\n"
            + (result.stderr or result.stdout)[-3000:]
        )


class OepTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        prepare_test_oedb(settings.dbname)
        return super().setup_databases(**kwargs)
