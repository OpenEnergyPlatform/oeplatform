"""
This module handles all relevant features that belong to specific sessions.
"""

from .error import APIError
from .actions import _get_engine, get_or_403

from random import randrange
import sys

_SESSION_CONTEXTS = {}


class SessionContext:

    def __init__(self, connection=None):
        engine = _get_engine()
        self.connection = engine.connect().connection
        self.connection._id = _add_entry(self, _SESSION_CONTEXTS)
        self.session_context = self
        self.cursors = {}

    def get_cursor(self, cursor_id):
        try:
            return self.cursors[cursor_id]
        except KeyError:
            raise APIError('Cursor not found %s'%cursor_id)

    def open_cursor(self):
            cursor = self.connection.cursor()
            cursor_id = _add_entry(cursor, self.cursors)
            return cursor_id

    def close_cursor(self, cursor_id):
        cursor = self.get_cursor(cursor_id)
        cursor.close()
        del self.cursors[cursor_id]
        print('Remaining cursors: ', self.cursors)

    def close(self):
        self.connection.close()
        del _SESSION_CONTEXTS[self.connection._id]


def load_cursor_from_context(context):
    session = load_session_from_context(context)
    cursor_id = get_or_403(context, 'cursor_id')
    return session.get_cursor(cursor_id)


def load_session_from_context(context):
    connection_id = get_or_403(context, 'connection_id')
    try:
        return _SESSION_CONTEXTS[connection_id]
    except KeyError:
        raise APIError("Connection (%s) not found" % connection_id)


def _add_entry(value, dictionary):
    key = randrange(0, sys.maxsize)
    while key in dictionary:
        key = randrange(0, sys.maxsize)
    dictionary[key] = value
    return key