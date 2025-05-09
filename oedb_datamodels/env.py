# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@gmail.com>
#
# SPDX-License-Identifier: MIT

from __future__ import with_statement

import os
import sys
from logging.config import fileConfig

import django
from alembic import context
from alembic.config import Config

from api.connection import _get_engine, get_connection_string
from base.structures import metadata as target_metadata

sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oeplatform.settings")
django.setup()


alembic_cfg = Config()
db_url = get_connection_string()
db_url = db_url.replace("%", "%%")
alembic_cfg.set_main_option("url", db_url)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata


if target_metadata.bind is None:
    target_metadata.bind = _get_engine()
# target_metadata.reflect()

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = _get_engine()

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
