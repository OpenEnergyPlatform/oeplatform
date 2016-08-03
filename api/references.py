# coding: utf-8
from sqlalchemy import Boolean, Column, create_engine, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base
import bibtexparser as btp

Base = declarative_base()
metadata = Base.metadata


class Entry(Base):
    __tablename__ = 'entries'
    __table_args__ = {'schema': 'reference'}

    entries_id = Column(Integer, primary_key=True, server_default=text(
        "nextval('reference.entries_entries_id_seq'::regclass)"))
    jabref_eid = Column(String(8),
                        server_default=text("NULL::character varying"))
    database_id = Column(ForeignKey('reference.jabref_database.database_id'))
    entry_types_id = Column(ForeignKey('reference.entry_types.entry_types_id'))
    cite_key = Column(String(100),
                      server_default=text("NULL::character varying"))
    abstract = Column(Text)
    address = Column(Text)
    annote = Column(Text)
    author = Column(Text)
    booktitle = Column(Text)
    chapter = Column(Text)
    comment = Column(Text)
    crossref = Column(Text)
    doi = Column(Text)
    edition = Column(Text)
    editor = Column(Text)
    eid = Column(Text)
    file = Column(Text)
    howpublished = Column(Text)
    institution = Column(Text)
    journal = Column(Text)
    key_ = Column(Text)
    keywords = Column(Text)
    language = Column(Text)
    location = Column(Text)
    month = Column(Text)
    note = Column(Text)
    number = Column(Text)
    organization = Column(Text)
    pages = Column(Text)
    pdf = Column(Text)
    pmid = Column(Text)
    priority = Column(Text)
    ps = Column(Text)
    publisher = Column(Text)
    qualityassured = Column(Text)
    ranking = Column(Text)
    relevance = Column(Text)
    school = Column(Text)
    search = Column(Text)
    series = Column(Text)
    title = Column(Text)
    type = Column(Text)
    url = Column(Text)
    volume = Column(Text)
    year = Column(Text)

    database = relationship('JabrefDatabase')
    entry_types = relationship('EntryType')


class EntryType(Base):
    __tablename__ = 'entry_types'
    __table_args__ = {'schema': 'reference'}

    entry_types_id = Column(Integer, primary_key=True, server_default=text(
        "nextval('reference.entry_types_entry_types_id_seq'::regclass)"))
    label = Column(Text)
    abstract = Column(String(3), server_default=text("NULL::character varying"))
    address = Column(String(3), server_default=text("NULL::character varying"))
    annote = Column(String(3), server_default=text("NULL::character varying"))
    author = Column(String(3), server_default=text("NULL::character varying"))
    booktitle = Column(String(3),
                       server_default=text("NULL::character varying"))
    chapter = Column(String(3), server_default=text("NULL::character varying"))
    comment = Column(String(3), server_default=text("NULL::character varying"))
    crossref = Column(String(3), server_default=text("NULL::character varying"))
    doi = Column(String(3), server_default=text("NULL::character varying"))
    edition = Column(String(3), server_default=text("NULL::character varying"))
    editor = Column(String(3), server_default=text("NULL::character varying"))
    eid = Column(String(3), server_default=text("NULL::character varying"))
    file = Column(String(3), server_default=text("NULL::character varying"))
    howpublished = Column(String(3),
                          server_default=text("NULL::character varying"))
    institution = Column(String(3),
                         server_default=text("NULL::character varying"))
    journal = Column(String(3), server_default=text("NULL::character varying"))
    key_ = Column(String(3), server_default=text("NULL::character varying"))
    keywords = Column(String(3), server_default=text("NULL::character varying"))
    language = Column(String(3), server_default=text("NULL::character varying"))
    location = Column(String(3), server_default=text("NULL::character varying"))
    month = Column(String(3), server_default=text("NULL::character varying"))
    note = Column(String(3), server_default=text("NULL::character varying"))
    number = Column(String(3), server_default=text("NULL::character varying"))
    organization = Column(String(3),
                          server_default=text("NULL::character varying"))
    pages = Column(String(3), server_default=text("NULL::character varying"))
    pdf = Column(String(3), server_default=text("NULL::character varying"))
    pmid = Column(String(3), server_default=text("NULL::character varying"))
    priority = Column(String(3), server_default=text("NULL::character varying"))
    ps = Column(String(3), server_default=text("NULL::character varying"))
    publisher = Column(String(3),
                       server_default=text("NULL::character varying"))
    qualityassured = Column(String(3),
                            server_default=text("NULL::character varying"))
    ranking = Column(String(3), server_default=text("NULL::character varying"))
    relevance = Column(String(3),
                       server_default=text("NULL::character varying"))
    school = Column(String(3), server_default=text("NULL::character varying"))
    search = Column(String(3), server_default=text("NULL::character varying"))
    series = Column(String(3), server_default=text("NULL::character varying"))
    title = Column(String(3), server_default=text("NULL::character varying"))
    type = Column(String(3), server_default=text("NULL::character varying"))
    url = Column(String(3), server_default=text("NULL::character varying"))
    volume = Column(String(3), server_default=text("NULL::character varying"))
    year = Column(String(3), server_default=text("NULL::character varying"))


class GroupType(Base):
    __tablename__ = 'group_types'
    __table_args__ = {'schema': 'reference'}

    group_types_id = Column(Integer, primary_key=True, server_default=text(
        "nextval('reference.group_types_group_types_id_seq'::regclass)"))
    label = Column(String(100), server_default=text("NULL::character varying"))


class Group(Base):
    __tablename__ = 'groups'
    __table_args__ = {'schema': 'reference'}

    groups_id = Column(Integer, primary_key=True, server_default=text(
        "nextval('reference.groups_groups_id_seq'::regclass)"))
    group_types_id = Column(Integer)
    label = Column(String(100), server_default=text("NULL::character varying"))
    database_id = Column(ForeignKey('reference.jabref_database.database_id'))
    parent_id = Column(Integer)
    search_field = Column(String(100),
                          server_default=text("NULL::character varying"))
    search_expression = Column(String(200),
                               server_default=text("NULL::character varying"))
    case_sensitive = Column(Boolean)
    reg_exp = Column(Boolean)
    hierarchical_context = Column(Integer)

    database = relationship('JabrefDatabase')


class JabrefDatabase(Base):
    __tablename__ = 'jabref_database'
    __table_args__ = {'schema': 'reference'}

    database_id = Column(Integer, primary_key=True, server_default=text(
        "nextval('reference.jabref_database_database_id_seq'::regclass)"))
    database_name = Column(String(64), nullable=False)
    md5_path = Column(String(32), nullable=False)



class CommentOnRow():
    origin = Column(String(1000), server_default=text("NULL::character varying"))
    method = Column(String(1000), server_default=text("NULL::character varying"))
#    assumptions = Column(JSON)

class String(Base):
    __tablename__ = 'strings'
    __table_args__ = {'schema': 'reference'}

    strings_id = Column(Integer, primary_key=True, server_default=text(
        "nextval('reference.strings_strings_id_seq'::regclass)"))
    label = Column(String(100), server_default=text("NULL::character varying"))
    content = Column(String(200),
                     server_default=text("NULL::character varying"))
    database_id = Column(ForeignKey('reference.jabref_database.database_id'))

    database = relationship('JabrefDatabase')




def read_bibtexfile(file_name):
    engine = create_engine(
        'postgres://ckan_perm:H6LgV#C&Mye(arGxQ2B-@localhost/test')
    metadata.create_all(bind=engine)
    sess = Session(bind=engine)

    with open(file_name) as bibtex_file:
        bibtex_database = btp.load(bibtex_file)
    for ent in bibtex_database.entries:
        props = {k.name: ent[k.name.replace('entries.', '')] for k in
                 Entry.__table__.c if k.name.replace('entries.', '') in ent}
        en = Entry(**props)
        sess.add(en)
    sess.commit()




if __name__ == '__main__':
    read_bibtexfile('test.bib')