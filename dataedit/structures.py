from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.orm import relationship
Base = declarative_base()
metadata = Base.metadata




class Tag(Base):
    __tablename__ = 'tags'
    __table_args__ = {'schema': 'public'}

    id = Column(BigInteger, primary_key=True)
    name = Column(String(40))
    color = Column(Integer)

class Table_tags(Base):
    __table_args__ = {'schema': 'public'}
    __tablename__ = 'table_tags'
    __table_args__ = (
        PrimaryKeyConstraint('tag', 'schema_name', 'table_name'),
    )
    tag = Column(ForeignKey(Tag.id))
    schema_name = Column(String(100))
    table_name = Column(String(100))


class EditBaseOld(Base):
    __table_args__ = {'schema': 'public'}
    __tablename__ = '_edit_base'
    _id = Column('_id', BigInteger, primary_key=True, nullable=False, autoincrement=True)
    _message = Column('_message', Text)
    _user = Column('_user', String(50))
    _submitted = Column('_submitted', DateTime, server_default=text("now()"))
    _autocheck = Column('_autocheck', Boolean, server_default=text("false"))
    _humancheck = Column('_humancheck', Boolean, server_default=text("false"))
    _type = Column('_type', String(8))
    _applied = Column('_applied', Boolean, server_default=text("false"))

class InsertBase(Base):
    __table_args__ = {'schema': 'public'}
    __tablename__ = '_insert_base'
    _id = Column('_id', BigInteger, primary_key=True, nullable=False, autoincrement=True)
    _message = Column('_message', Text)
    _user = Column('_user', String(50))
    _submitted = Column('_submitted', DateTime, server_default=text("now()"))
    _autocheck = Column('_autocheck', Boolean, server_default=text("false"))
    _humancheck = Column('_humancheck', Boolean, server_default=text("false"))
    _type = Column('_type', String(8))
    _applied = Column('_applied', Boolean, server_default=text("false"))