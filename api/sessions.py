"""This module handles all relevant features that belong to specific sessions.

SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import sys
import time
from random import randrange

from django.contrib.auth.models import AbstractUser

from api.actions import get_or_403
from api.error import APIError
from oedb.connection import _get_engine
from oeplatform.settings import ANON_CONNECTION_LIMIT, TIME_OUT, USER_CONNECTION_LIMIT

_SESSION_CONTEXTS = {}


class SessionContext:
    def __init__(self, connection_id=None, owner: AbstractUser | None = None):
        user_connections = 0
        current_time = time.time()

        self.last_activity = current_time
        for sid in dict(_SESSION_CONTEXTS):
            try:
                sess = _SESSION_CONTEXTS[sid]
                if current_time - sess.last_activity > TIME_OUT and not sess.cursors:
                    sess.close()
                else:
                    if sess.owner == owner:
                        user_connections += 1
            except KeyError:
                pass

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

        engine = _get_engine()
        self.connection = engine.connect().connection
        if connection_id is None:
            connection_id = _add_entry(self, _SESSION_CONTEXTS)
        elif connection_id not in _SESSION_CONTEXTS:
            _SESSION_CONTEXTS[connection_id] = self
        else:
            raise Exception("Tried to open existing")
        self.owner = owner
        self.connection._id = connection_id
        self.session_context = self
        self.cursors = {}

    def get_cursor(self, cursor_id):
        try:
            return self.cursors[cursor_id]
        except KeyError:
            raise APIError("Cursor not found %s" % cursor_id)

    def open_cursor(self, named=False):
        cursor_id = _get_new_key(self.cursors)
        if named:
            cursor = self.connection.cursor(name=str(cursor_id))
        else:
            cursor = self.connection.cursor()
        self.cursors[cursor_id] = cursor
        return cursor_id

    def close_cursor(self, cursor_id):
        cursor = self.get_cursor(cursor_id)
        cursor.close()
        del self.cursors[cursor_id]

    def close(self):
        self.connection.close()
        if self.connection._id in _SESSION_CONTEXTS:
            del _SESSION_CONTEXTS[self.connection._id]

    def rollback(self):
        self.connection.rollback()
        if not self.cursors:
            self.close()


def close_all_for_user(owner):
    if owner.is_anonymous:
        raise PermissionError
    for sid in dict(_SESSION_CONTEXTS):
        try:
            sess = _SESSION_CONTEXTS[sid]
            if sess.owner == owner:
                for cursor_id in dict(sess.cursors):
                    if cursor_id in sess.cursors:
                        sess.cursors[cursor_id].close()
                sess.close()
        except KeyError:
            pass


def load_cursor_from_context(context):
    session = load_session_from_context(context)
    cursor_id = get_or_403(context, "cursor_id")
    return session.get_cursor(cursor_id)


def load_session_from_context(context):
    connection_id = get_or_403(context, "connection_id")
    user = context.get("user")
    try:
        sess = _SESSION_CONTEXTS[connection_id]
        sess.last_activity = time.time()
        if user and sess.owner != user:
            raise PermissionError
        return sess
    except KeyError:
        return SessionContext(connection_id=connection_id, owner=user)


def _get_new_key(dictionary):
    key = randrange(0, sys.maxsize)
    while key in dictionary:
        key = randrange(0, sys.maxsize)
    return key


def _add_entry(value, dictionary, key=None):
    if key is None:
        key = _get_new_key(dictionary)
    dictionary[key] = value
    return key
