"""This module handles all relevant features that belong to specific sessions."""

__license__ = """
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import sys
import threading
import time
from random import randrange

from django.contrib.auth.models import AbstractUser

from api.error import APIError
from api.utils import get_or_403
from oedb.connection import AbstractCursor, DBAPIConnection, _get_engine
from oeplatform.settings import ANON_CONNECTION_LIMIT, TIME_OUT, USER_CONNECTION_LIMIT

# Finished sessions, by connection id. Every reader expects a finished object.
_SESSION_CONTEXTS = {}

# Sessions that have been counted and given an id but are still opening their
# connection, as connection id -> owner. They count against the limit and hold
# their id, but stay out of `_SESSION_CONTEXTS` until they are finished.
_PENDING = {}

# Guards both dicts: every read that decides something and every mutation of
# either takes it, so counting and reserving are one operation and the limits
# below are exact rather than likely -- issue #2492.
#
# It is never held while a connection is opened or closed. `engine.connect()`
# can block on the pool, and a module lock across it would queue every request
# in the process behind the slowest one.
#
# The count is per interpreter, because these dicts are. One account's real
# ceiling is therefore `processes x USER_CONNECTION_LIMIT` (or
# `ANON_CONNECTION_LIMIT`), where `processes` is the size of the mod_wsgi
# daemon group serving /api/v0/advanced. The limits are a real ceiling while
# that group runs one process -- which it must anyway, since a session opened
# in one process is invisible to the next. That size is set in the host's
# Apache configuration, not here. A limit that holds across processes needs
# shared state and is not built.
_LOCK = threading.Lock()


class SessionContext:
    # A half-built session must still answer for an owner. The constructor
    # assigns this before the object is published (see below), but the
    # ordering is the kind of thing a later refactor reorders, and every
    # reader of `_SESSION_CONTEXTS` catches `KeyError` only -- a missing
    # attribute would reach the caller as a 500.
    owner: AbstractUser | None = None

    def __init__(self, connection_id=None, owner: AbstractUser | None = None):
        self.last_activity = time.time()
        self.owner = owner
        self.session_context = self
        self.cursors = {}

        _close_sessions(_take_expired(self.last_activity))

        # Counting and reserving happen under the lock; opening the connection
        # does not. A reservation holds its place in the count and its id, so
        # it is given back whatever stops the connection from opening.
        connection_id = _reserve(connection_id, owner)
        try:
            engine = _get_engine()
            connection = engine.connect()
            self.connection: DBAPIConnection = connection.connection  # type: ignore

            # FIXME: is this a good idea, to add a custom attribute?
            setattr(self.connection, "_id", connection_id)
        except BaseException:
            with _LOCK:
                del _PENDING[connection_id]
            raise

        # Publishing is deliberately the last statement of __init__: from here
        # on the session is reachable from every other thread, and the readers
        # of `_SESSION_CONTEXTS` expect a finished object.
        with _LOCK:
            del _PENDING[connection_id]
            _add_entry(self, _SESSION_CONTEXTS, connection_id)

    def get_cursor(self, cursor_id) -> AbstractCursor:
        try:
            return self.cursors[cursor_id]
        except KeyError:
            raise APIError("Cursor not found %s" % cursor_id)

    def open_cursor(self, named: bool = False):
        cursor_id = _get_new_key(self.cursors)
        if named:
            cursor = self.connection.cursor(name=str(cursor_id))
        else:
            cursor = self.connection.cursor()
        self.cursors[cursor_id] = cursor
        return cursor_id

    def close_cursor(self, cursor_id) -> None:
        cursor = self.get_cursor(cursor_id)
        cursor.close()
        del self.cursors[cursor_id]

    def close(self) -> None:
        self.connection.close()
        with _LOCK:
            # by identity: a sweep or `close_all_for_user` may already have
            # taken this session out, and its id been given to a new one since
            if _SESSION_CONTEXTS.get(self.connection._id) is self:
                del _SESSION_CONTEXTS[self.connection._id]

    def rollback(self) -> None:
        self.connection.rollback()
        if not self.cursors:
            self.close()


def close_all_for_user(owner: AbstractUser) -> None:
    if owner.is_anonymous:
        raise PermissionError
    with _LOCK:
        owned = [s for s in _SESSION_CONTEXTS.values() if s.owner == owner]
        for sess in owned:
            del _SESSION_CONTEXTS[sess.connection._id]
    _close_sessions(owned, with_cursors=True)


def load_cursor_from_context(context: dict) -> AbstractCursor:
    session = load_session_from_context(context)
    cursor_id = get_or_403(context, "cursor_id")
    return session.get_cursor(cursor_id)


def load_session_from_context(context: dict) -> SessionContext:
    connection_id = get_or_403(context, "connection_id")
    user = context.get("user")
    with _LOCK:
        sess = _SESSION_CONTEXTS.get(connection_id)
    if sess is None:
        return SessionContext(connection_id=connection_id, owner=user)
    sess.last_activity = time.time()
    if user and sess.owner != user:
        raise PermissionError
    return sess


def _take_expired(now: float) -> list[SessionContext]:
    """Unregister the idle sessions, for the caller to close outside the lock."""
    with _LOCK:
        expired = [
            sess
            for sess in _SESSION_CONTEXTS.values()
            if now - sess.last_activity > TIME_OUT and not sess.cursors
        ]
        for sess in expired:
            del _SESSION_CONTEXTS[sess.connection._id]
    return expired


def _reserve(connection_id, owner: AbstractUser | None):
    """Count the owner's sessions and, if there is room, reserve one more.

    Returns the reserved connection id. Refuses with `APIError` when the owner
    is at the limit, and raises when the requested id is already taken.
    """
    with _LOCK:
        user_connections = sum(
            1 for sess in _SESSION_CONTEXTS.values() if sess.owner == owner
        ) + sum(1 for pending in _PENDING.values() if pending == owner)

        if not owner or owner.is_anonymous:
            if user_connections >= ANON_CONNECTION_LIMIT:
                raise APIError(
                    "Connection limit for anonymous users is exceeded"
                    ". Please login to get your own connection pool."
                )
        else:
            if user_connections >= USER_CONNECTION_LIMIT:
                raise APIError(
                    "This user exceeded the connection limit."
                    "If you are using the oedialect, this may be "
                    "caused by a known bug that has been fixed in"
                    "v0.0.5.dev0. You can close al your connections"
                    "manually at https://openenergy-platform.org/api/v0/advanced/connection/close_all"  # noqa
                )

        taken = _SESSION_CONTEXTS.keys() | _PENDING.keys()
        if connection_id is None:
            connection_id = _get_new_key(taken)
        elif connection_id in taken:
            raise Exception("Tried to open existing")

        _PENDING[connection_id] = owner
    return connection_id


def _close_sessions(sessions: list[SessionContext], with_cursors=False) -> None:
    """Close every session given, then raise the first failure if there was one.

    The sessions are already unregistered, so one that is skipped here is never
    closed by anything.
    """
    failure = None
    for sess in sessions:
        try:
            if with_cursors:
                for cursor in list(sess.cursors.values()):
                    cursor.close()
            sess.close()
        except Exception as error:
            failure = failure or error
    if failure is not None:
        raise failure


def _get_new_key(dictionary: dict):
    key = randrange(0, sys.maxsize)
    while key in dictionary:
        key = randrange(0, sys.maxsize)
    return key


def _add_entry(value, dictionary: dict, key):
    dictionary[key] = value
    return key
