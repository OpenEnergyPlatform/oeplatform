"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.

SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import logging
import re
from typing import Iterable

from oedb.connection import _get_engine, _get_inspector
from oeplatform.settings import SCHEMA_DATA, SCHEMA_DEFAULT, SCHEMA_DEFAULT_TEST_SANDBOX

logger = logging.getLogger("oeplatform")

ID_COLUMN_NAME = "id"

MAX_IDENTIFIER_LENGTH = 63
MAX_COL_NAME_LENGTH = MAX_IDENTIFIER_LENGTH
MAX_TABLE_NAME_LENGTH = MAX_IDENTIFIER_LENGTH
MAX_SCHEMA_NAME_LENGTH = MAX_IDENTIFIER_LENGTH

MAX_NAME_LENGTH = 50  # postgres limit minus pre/suffix for meta tables
NAME_PATTERN = re.compile("^[a-z][a-z0-9_]{0,%s}$" % (MAX_NAME_LENGTH - 1))
META_TABLE_TYPES = ["edit", "insert", "delete"]


def is_valid_identifier(name: str) -> bool:
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


class _OedbTable:
    """represents data table and meta tables in postgres oedb."""

    def __init__(self, validated_table_name: str, validated_schema_name: str):
        self._schema = _OedbSchema(validated_schema_name=validated_schema_name)
        self._validated_table_name = clip_table_name(validated_table_name)
        self._engine = _get_engine()

    @property
    def _quoted_name(self) -> str:
        return f'"{self._schema}"."{self._validated_table_name}"'

    def drop_if_exists(self) -> None:
        sql = f"DROP TABLE IF EXISTS {self._quoted_name} CASCADE;"
        logger.warning(sql)
        self._engine.execute(sql)


class OedbTableGroup:
    """represents data table and meta tables in postgres oedb."""

    def __init__(self, validated_table_name: str, schema_name: str | None = None):
        """
        Parameters
        ----------
        validated_table_name : str
            user must ensure name is valid, because we have historic tables
            that dont comply with NAME_PATTERN

        schema_name : str | None, optional
            physical schema in oedb

        """

        # check schema
        schema_name = schema_name or SCHEMA_DEFAULT
        if schema_name not in {SCHEMA_DATA, SCHEMA_DEFAULT_TEST_SANDBOX}:
            raise ValueError(f"Invalid schema: {schema_name}")

        # readonly properties
        self._table = _OedbTable(
            validated_table_name=validated_table_name,
            validated_schema_name=schema_name,
        )

        self._meta_tables = {
            t: _OedbTable(
                validated_table_name=f"_{validated_table_name}_{t}",
                validated_schema_name=f"_{schema_name}",
            )
            for t in META_TABLE_TYPES
        }

    def drop_if_exists(self) -> None:
        tables = list(self._meta_tables.values()) + [self._table]  # main table last
        for table in tables:
            table.drop_if_exists()
