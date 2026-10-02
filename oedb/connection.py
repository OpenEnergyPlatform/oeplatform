"""Contains functions to interact with the postgres oedb.

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from contextlib import contextmanager
from typing import Any, Iterable, Iterator, List, Optional, Protocol

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


# The pool is bounded PER PROCESS while the database ceiling is per cluster,
# and nothing in this process can see how many processes there are. Production
# runs 13 mod_wsgi daemon processes (12 in the main group, 1 for
# /api/v0/advanced) against `max_connections = 255` with 8 reserved, so the
# budget is 247 and the arithmetic is:
#
#     13 processes x (pool_size + max_overflow) = 13 x 17 = 221  <  247
#
# The old values were pool_size=0 (unbounded retention) and max_overflow=200,
# i.e. 2,600 against 255 -- ten times the database. That ceiling was reached in
# production on 2026-09-10 and the platform refused connections for twelve days
# (issue #2495).
#
# A healthy platform uses about 12 connections across all 13 processes, so
# these numbers are a safety net rather than an allocation. max_overflow=15
# still exceeds `threads=15`, so request-scoped work never queues on the pool.
#
# IF THE PROCESS COUNT CHANGES, THIS ARITHMETIC CHANGES. That count lives in
# `/data/httpd/conf/oep.conf` on the production host, which is in no repository
# and has already been changed twice in 2026 (1 -> 4 -> 12).
#
# pool_pre_ping: the pool discards a connection for being old, never for
# being dead, so without this a connection Postgres or the network has already
# closed is handed to the next request, which fails with a generic 400 while
# the retry succeeds -- issue #2488. The cost is one round trip per checkout.
OEDB_POOL_SIZE = 2
OEDB_MAX_OVERFLOW = 15

__ENGINE = create_engine(
    __get_connection_string(),
    pool_size=OEDB_POOL_SIZE,
    pool_recycle=600,
    max_overflow=OEDB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

_SA_METADATA = MetaData(bind=__ENGINE)


def _get_engine() -> Engine:
    return __ENGINE


def _get_inspector() -> Inspector:
    return inspect(_get_engine())  # type: ignore


def _create_oedb_session() -> Session:
    """Return a sqlalchemy session to the oedb

    Should only be created once per user request.

    Prefer `oedb_session()`: a session closed only on the success path leaks
    its connection, with its transaction still open, whenever anything raises.
    """
    return sessionmaker(bind=_get_engine())()


@contextmanager
def oedb_session() -> Iterator[Session]:
    """A session that is returned to the pool however the block ends.

    This is the leak fix for issue #2495. Callers used to close on the success
    path only, so any exception between opening and closing left the
    connection checked out for the life of the process -- and `idle in
    transaction`, which also holds back autovacuum across the whole database.
    Measured at roughly 17 leaked connections a day, which exhausted a
    255-connection cluster in about a fortnight.
    """
    session = _create_oedb_session()
    try:
        yield session
    finally:
        session.close()


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
