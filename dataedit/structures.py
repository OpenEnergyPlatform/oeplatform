import re

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.sql.expression import func

from base.structures import Base


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {"schema": "public"}

    id = Column(BigInteger, primary_key=True)
    name = Column(String(40))
    color = Column(Integer)
    usage_count = Column(BigInteger, server_default="0")
    usage_tracked_since = Column(DateTime(), server_default=func.now())
    name_normalized = Column(String(40), nullable=False, unique=True)
    default_color = int("2E3638", 16)

    def __init__(self, **kwargs):
        # sanitize name, auto fill name_normalized
        kwargs["name"] = self.create_name_clean(kwargs["name"])
        kwargs["name_normalized"] = self.create_name_normalized(kwargs["name"])
        kwargs["color"] = kwargs.get("color", self.default_color)
        super().__init__(**kwargs)

    @staticmethod
    def create_name_normalized(name):
        """
        Args:
            name(str): tag name

        Returns:
            str: normalized tag name

        Example:
            >>> create_name_normalized(" not a good  TAG")
            'not_a_good_tag'
        """
        name_norm = name or ""
        name_norm = name_norm.lower()
        name_norm = re.sub("[^a-z0-9]+", "_", name_norm)
        name_norm = name_norm.strip("_")
        name_norm = name_norm[:40]  # max len
        return name_norm

    @staticmethod
    def create_name_clean(name):
        """
        Args:
            name(str): tag name

        Returns:
            str: sanitized tag name

        Example:
            >>> create_name_clean(" not a good  TAG")
            'not a good TAG'
        """
        name_norm = name or ""
        re.sub(r"\s+", " ", name_norm)
        name_norm = name_norm.strip()
        return name_norm


class TableTags(Base):
    __tablename__ = "table_tags"
    __table_args__ = (
        PrimaryKeyConstraint(
            "tag", "schema_name", "table_name", name="table_tags_pkey"
        ),
        {"schema": "public"},
    )
    tag = Column(ForeignKey(Tag.id, name="table_tags_tag_fkey"))
    schema_name = Column(String(100))
    table_name = Column(String(100))


class EditBaseOld(Base):
    __table_args__ = {"schema": "public"}
    __tablename__ = "_edit_base"
    _id = Column(
        "_id", BigInteger, primary_key=True, nullable=False, autoincrement=True
    )
    _message = Column("_message", Text, nullable=False)
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


class MetaSearch(Base):
    __table_args__ = {"schema": "public"}
    __tablename__ = "meta_search"
    schema = Column("schema", String(100), primary_key=True)
    table = Column("table", String(100), primary_key=True)
    comment = Column("comment", TSVECTOR)
