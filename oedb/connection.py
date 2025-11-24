"""Contains functions to interact with the postgres oedb.

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from typing import Any, Iterable, List, Optional, Protocol

from sqlalchemy import MetaData, create_engine, inspect
from sqlalchemy.engine import ResultProxy
from sqlalchemy.engine.base import Connection  # from engine.connect()
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm.session import Session, sessionmaker
from sqlalchemy.pool.base import (
    _ConnectionFairy as DBAPIConnection,  # from engine.connect().connection
)

from oeplatform.settings import dbhost, dbname, dbpasswd, dbport, dbuser

__all__ = ["Connection", "ResultProxy", "DBAPIConnection", "AbstractCursor"]


def __get_connection_string():
    return "postgresql://{0}:{1}@{2}:{3}/{4}".format(
        dbuser, dbpasswd, dbhost, dbport, dbname
    )


__ENGINE = create_engine(
    __get_connection_string(), pool_size=0, pool_recycle=600, max_overflow=200
)

__SA_METADATA = MetaData(bind=__ENGINE)


def _get_engine() -> Engine:
    return __ENGINE


def _get_inspector() -> Inspector:
    return inspect(_get_engine())  # type: ignore


def _create_oedb_session() -> Session:
    """Return a sqlalchemy session to the oedb

    Should only be created once per user request.
    """
    return sessionmaker(bind=_get_engine())()


class AbstractColumn(Protocol):
    """this is only for type checking"""

    name: str
    type_code: int
    display_size: int
    internal_size: int
    precision: int
    scale: int
    null_ok: bool


class AbstractCursor(Protocol):
    """there is no real cursor class, this is only for type checking"""

    description: List[AbstractColumn]
    rowcount: int
    statusmessage: str

    def execute(self, operation: str, parameters: Any = ...) -> Any: ...  # noqa:E704
    def fetchone(self) -> Optional[ResultProxy]: ...  # noqa:E704
    def fetchall(self) -> Iterable[ResultProxy]: ...  # noqa:E704
    def fetchmany(self, size: int = ...) -> Iterable[ResultProxy]: ...  # noqa:E704
    def close(self) -> None: ...  # noqa:E704
