"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import re
from typing import Iterable, Literal, get_args

from sqlalchemy import MetaData, Table

from login.permissions import ADMIN_PERM, DELETE_PERM, NO_PERM
from oedb.connection import _get_engine, _get_inspector
from oedb.structures import EditBase
from oeplatform.settings import SCHEMA_DATA, SCHEMA_DEFAULT, SCHEMA_DEFAULT_TEST_SANDBOX

logger = logging.getLogger("oeplatform")

ID_COLUMN_NAME = "id"

MAX_IDENTIFIER_LENGTH = 63
MAX_COL_NAME_LENGTH = MAX_IDENTIFIER_LENGTH
MAX_TABLE_NAME_LENGTH = MAX_IDENTIFIER_LENGTH
MAX_SCHEMA_NAME_LENGTH = MAX_IDENTIFIER_LENGTH

MAX_NAME_LENGTH = 50  # postgres limit minus pre/suffix for meta tables
NAME_PATTERN = re.compile("^[a-z][a-z0-9_]{0,%s}$" % (MAX_NAME_LENGTH - 1))

MetaActionType = Literal["edit", "insert", "delete"]


class PermissionError(Exception):
    pass


def is_valid_name(name: str) -> bool:
    return len(name) <= MAX_NAME_LENGTH and bool(NAME_PATTERN.match(name))


def clip_table_name(name: str) -> str:
    if len(name) > MAX_TABLE_NAME_LENGTH:
        name = name[:MAX_TABLE_NAME_LENGTH]
    return name


class _OedbSchema:
    """represents schema in postgres oedb."""

    def __init__(self, validated_schema_name: str):
        self._validated_schema_name = validated_schema_name

    def __str__(self):
        return self._validated_schema_name

    def get_table_names(self) -> Iterable[str]:
        return _get_inspector().get_table_names(schema=self._validated_schema_name)

    def get_oedb_tables(
        self, permission_level: int = NO_PERM
    ) -> Iterable["_OedbTable"]:
        return [
            _OedbTable(
                validated_table_name=table_name,
                validated_schema_name=self._validated_schema_name,
                permission_level=permission_level,
            )
            for table_name in self.get_table_names()
        ]

    def get_meta_schema(self) -> "_OedbSchema":
        return _OedbSchema(validated_schema_name=f"_{self._validated_schema_name}")


class _OedbTable:
    """represents data table and meta tables in postgres oedb."""

    def __init__(
        self,
        validated_table_name: str,
        validated_schema_name: str,
        permission_level: int = NO_PERM,
    ):
        self._permission_level = permission_level
        self._schema = _OedbSchema(validated_schema_name=validated_schema_name)
        self._validated_table_name = clip_table_name(validated_table_name)
        self._engine = _get_engine()

    @property
    def name(self) -> str:
        return self._validated_table_name

    @property
    def schema_name(self) -> str:
        return self._validated_schema_name

    @property
    def _quoted_name(self) -> str:
        return f'"{self._schema}"."{self._validated_table_name}"'

    @property
    def _validated_schema_name(self) -> str:
        return self._schema._validated_schema_name

    def drop_if_exists(self) -> None:
        # IMPORTANT: this should be the only place where we delete
        # tables in oedb
        # we coud also do self._sa_table.drop(checkfirst=True),
        # but i don't think it does CASCADE
        sql = f"DROP TABLE IF EXISTS {self._quoted_name} CASCADE;"
        return self._execute(sql, requires_permission=DELETE_PERM)

    def exists(self) -> bool:
        return bool(
            self._engine.dialect.has_table(
                self._engine,
                self._validated_table_name,
                schema=self._validated_schema_name,
            )
        )

    @property
    def _sa_table(self) -> Table:
        metadata = MetaData(bind=self._engine)
        return Table(
            self._validated_table_name,
            metadata,
            autoload=True,
            schema=self._validated_schema_name,
        )

    def _execute(self, query, requires_permission: int = ADMIN_PERM):
        if self._permission_level < requires_permission:
            raise PermissionError()
        return self._engine.execute(query)

    def __str__(self) -> str:
        return self._quoted_name


class _OedbMainTable(_OedbTable):
    pass


class _OedbMetaTable(_OedbTable):
    def __init__(
        self,
        action: MetaActionType,
        validated_main_table_name: str,
        validated_main_schema_name: str,
        permission_level: int = NO_PERM,
    ):
        assert action in set(get_args(MetaActionType))
        self._action = action
        self._main_table = _OedbMainTable(
            validated_table_name=validated_main_table_name,
            validated_schema_name=validated_main_schema_name,
            permission_level=permission_level,
        )

        super().__init__(
            validated_table_name=f"_{validated_main_table_name}_{action}",
            validated_schema_name=f"_{validated_main_schema_name}",
            permission_level=permission_level,
        )

    def _create(self, include_indexes: bool = True) -> None:
        query = (
            f'CREATE TABLE "{self.schema_name}"."{self.name}" (LIKE '
            f'"{self._main_table.schema_name}"."{self._main_table.name}"'
        )
        if include_indexes:
            query += "INCLUDING ALL EXCLUDING INDEXES, PRIMARY KEY (_id) "
        query += f") INHERITS ({EditBase.__tablename__});"
        return self._execute(query, requires_permission=ADMIN_PERM)

    def create_if_missing(self, include_indexes: bool = True) -> None:
        if not self.exists():
            self._create(include_indexes=include_indexes)


class OedbTableGroup:
    """represents data table and meta tables in postgres oedb."""

    def __init__(
        self,
        validated_table_name: str,
        schema_name: str | None = None,
        permission_level: int = NO_PERM,
    ):
        """
        Parameters
        ----------
        validated_table_name : str
            user must ensure name is valid, because we have historic tables
            that dont comply with NAME_PATTERN

        schema_name : str | None, optional
            physical schema in oedb

        """

        self._permission_level = permission_level

        # check schema
        schema_name = schema_name or SCHEMA_DEFAULT
        if schema_name not in {SCHEMA_DATA, SCHEMA_DEFAULT_TEST_SANDBOX}:
            raise ValueError(f"Invalid schema: {schema_name}")

        # readonly properties
        self._table = _OedbMainTable(
            validated_table_name=validated_table_name,
            validated_schema_name=schema_name,
            permission_level=self._permission_level,
        )

        self._meta_tables = {
            a: _OedbMetaTable(
                action=a,
                validated_main_schema_name=schema_name,
                validated_main_table_name=validated_table_name,
                permission_level=self._permission_level,
            )
            for a in get_args(_OedbMetaTable)
        }

    @property
    def meta_table_names(self) -> dict[str, str]:
        return {
            action: t._validated_table_name for action, t in self._meta_tables.items()
        }

    def exists(self) -> bool:
        # only check main table
        return self._table.exists()

    def drop_if_exists(self) -> None:
        tables = list(self._meta_tables.values()) + [self._table]  # main table last
        for table in tables:
            table.drop_if_exists()
