"""
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class EditBase(Base):
    __table_args__ = {"schema": "public"}
    __tablename__ = "_edit_base"
    _id = Column(
        "_id",
        BigInteger,
        Sequence("_edit_base__id_seq"),
        primary_key=True,
        nullable=False,
        autoincrement=True,
    )
    _message = Column("_message", String(500), nullable=True)
    _user = Column("_user", String(50), nullable=False)
    _submitted = Column(
        "_submitted", DateTime, nullable=False, server_default=text("now()")
    )
    _autocheck = Column(
        "_autocheck", Boolean, nullable=False, server_default=text("false")
    )
    _humancheck = Column(
        "_humancheck", Boolean, nullable=False, server_default=text("false")
    )
    _type = Column("_type", String(8), nullable=False)
    _applied = Column("_applied", Boolean, nullable=False, server_default=text("false"))


class InsertBase(Base):
    __table_args__ = {"schema": "public"}
    __tablename__ = "_insert_base"
    _id = Column(
        "_id", BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    _message = Column("_message", Text)
    _user = Column("_user", String(50))
    _submitted = Column("_submitted", DateTime, server_default=text("now()"))
    _autocheck = Column("_autocheck", Boolean, server_default=text("false"))
    _humancheck = Column("_humancheck", Boolean, server_default=text("false"))
    _type = Column("_type", String(8))
    _applied = Column("_applied", Boolean, server_default=text("false"))


class ApiConstraint(Base):
    __table_args__ = {"schema": "public"}
    __tablename__ = "api_constraints"

    id = Column(BigInteger, primary_key=True, nullable=False)
    action = Column(String(100))
    constraint_type = Column(String(100))
    constraint_name = Column(String(100))
    constraint_parameter = Column(String(100))
    reference_table = Column(String(100))
    reference_column = Column(String(100))
    c_schema = Column(String(100))
    c_table = Column(String(100))
    reviewed = Column(Boolean, default=False)
    changed = Column(Boolean, default=False)


class ApiColumn(Base):
    __table_args__ = {"schema": "public"}
    __tablename__ = "api_columns"

    id = Column(BigInteger, primary_key=True, nullable=False)
    column_name = Column(String(50))
    not_null = Column(Boolean)
    data_type = Column(String(50))
    new_name = Column(String(50))
    reviewed = Column(Boolean, default=False)
    changed = Column(Boolean, default=False)
    c_schema = Column(String(50))
    c_table = Column(String(50))
