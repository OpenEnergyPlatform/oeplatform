"""
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, Text, text

from base.structures import Base


class EditBaseOld(Base):
    __table_args__ = {"schema": "public"}
    __tablename__ = "_edit_base"
    _id = Column(
        "_id", BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    _message = Column("_message", Text, nullable=True)
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
