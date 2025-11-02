"""Contains functions to interact with the postgres oedb.

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import sqlalchemy as sqla

from oeplatform.settings import dbhost, dbname, dbpasswd, dbport, dbuser


def __get_connection_string():
    return "postgresql://{0}:{1}@{2}:{3}/{4}".format(
        dbuser, dbpasswd, dbhost, dbport, dbname
    )


__ENGINE = sqla.create_engine(
    __get_connection_string(), pool_size=0, pool_recycle=600, max_overflow=200
)


def _get_engine():
    return __ENGINE
