from egoio.db_tables import reference as ref


class ArticleForm:
    def __init__(self, author, title, journal, year, entry_types_id,
                 volume=None, number=None, pages=None, month=None, note=None):
        self.author = author
        self.title = title
        self.journal = journal
        self.year = year
        self.entry_types_id = entry_types_id
        self.volume = volume
        self.number = number
        self.pages = pages
        self.month = month
        self.note = note

    def save(self, session):
        entry = ref.Entry(author=self.author, title=self.title,
                          journal=self.journal, year=self.year,
                          entry_types_id=self.entry_types_id,
                          volume=self.volume, number=self.number,
                          pages=self.pages, month=self.month, note=self.note)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'author': self.author, 'title': self.title,
             'journal': self.journal, 'year': self.year,
             'entry_types_id': self.entry_types_id, 'volume': self.volume,
             'number': self.number, 'pages': self.pages, 'month': self.month,
             'note': self.note})


class BookForm:
    def __init__(self, title, publisher, year, entry_types_id, author=None,
                 editor=None, series=None, address=None, edition=None,
                 month=None, note=None, isbn=None, volume=None, number=None):
        self.title = title
        self.publisher = publisher
        self.year = year
        self.entry_types_id = entry_types_id
        self.author = author
        self.editor = editor
        self.series = series
        self.address = address
        self.edition = edition
        self.month = month
        self.note = note
        self.isbn = isbn
        self.volume = volume
        self.number = number

    def save(self, session):
        entry = ref.Entry(title=self.title, publisher=self.publisher,
                          year=self.year, entry_types_id=self.entry_types_id,
                          author=self.author, editor=self.editor,
                          series=self.series, address=self.address,
                          edition=self.edition, month=self.month,
                          note=self.note, isbn=self.isbn, volume=self.volume,
                          number=self.number)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'title': self.title, 'publisher': self.publisher,
             'year': self.year, 'entry_types_id': self.entry_types_id,
             'author': self.author, 'editor': self.editor,
             'series': self.series, 'address': self.address,
             'edition': self.edition, 'month': self.month, 'note': self.note,
             'isbn': self.isbn, 'volume': self.volume, 'number': self.number})


class BookletForm:
    def __init__(self, title, entry_types_id, author=None, howpublished=None,
                 address=None, month=None, year=None, note=None):
        self.title = title
        self.entry_types_id = entry_types_id
        self.author = author
        self.howpublished = howpublished
        self.address = address
        self.month = month
        self.year = year
        self.note = note

    def save(self, session):
        entry = ref.Entry(title=self.title, entry_types_id=self.entry_types_id,
                          author=self.author, howpublished=self.howpublished,
                          address=self.address, month=self.month,
                          year=self.year, note=self.note)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'title': self.title, 'entry_types_id': self.entry_types_id,
             'author': self.author, 'howpublished': self.howpublished,
             'address': self.address, 'month': self.month, 'year': self.year,
             'note': self.note})


class ConferenceForm:
    def __init__(self, author, title, booktitle, year, entry_types_id,
                 editor=None, series=None, pages=None, address=None, month=None,
                 organization=None, publisher=None, note=None, volume=None,
                 number=None):
        self.author = author
        self.title = title
        self.booktitle = booktitle
        self.year = year
        self.entry_types_id = entry_types_id
        self.editor = editor
        self.series = series
        self.pages = pages
        self.address = address
        self.month = month
        self.organization = organization
        self.publisher = publisher
        self.note = note
        self.volume = volume
        self.number = number

    def save(self, session):
        entry = ref.Entry(author=self.author, title=self.title,
                          booktitle=self.booktitle, year=self.year,
                          entry_types_id=self.entry_types_id,
                          editor=self.editor, series=self.series,
                          pages=self.pages, address=self.address,
                          month=self.month, organization=self.organization,
                          publisher=self.publisher, note=self.note,
                          volume=self.volume, number=self.number)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'author': self.author, 'title': self.title,
             'booktitle': self.booktitle, 'year': self.year,
             'entry_types_id': self.entry_types_id, 'editor': self.editor,
             'series': self.series, 'pages': self.pages,
             'address': self.address, 'month': self.month,
             'organization': self.organization, 'publisher': self.publisher,
             'note': self.note, 'volume': self.volume, 'number': self.number})


class InbookForm:
    def __init__(self, title, publisher, year, entry_types_id, chapter=None,
                 pages=None, author=None, editor=None, series=None, type=None,
                 address=None, edition=None, month=None, note=None, volume=None,
                 number=None):
        self.title = title
        self.publisher = publisher
        self.year = year
        self.entry_types_id = entry_types_id
        self.chapter = chapter
        self.pages = pages
        self.author = author
        self.editor = editor
        self.series = series
        self.type = type
        self.address = address
        self.edition = edition
        self.month = month
        self.note = note
        self.volume = volume
        self.number = number

    def save(self, session):
        entry = ref.Entry(title=self.title, publisher=self.publisher,
                          year=self.year, entry_types_id=self.entry_types_id,
                          chapter=self.chapter, pages=self.pages,
                          author=self.author, editor=self.editor,
                          series=self.series, type=self.type,
                          address=self.address, edition=self.edition,
                          month=self.month, note=self.note, volume=self.volume,
                          number=self.number)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'title': self.title, 'publisher': self.publisher,
             'year': self.year, 'entry_types_id': self.entry_types_id,
             'chapter': self.chapter, 'pages': self.pages,
             'author': self.author, 'editor': self.editor,
             'series': self.series, 'type': self.type, 'address': self.address,
             'edition': self.edition, 'month': self.month, 'note': self.note,
             'volume': self.volume, 'number': self.number})


class IncollectionForm:
    def __init__(self, author, title, booktitle, publisher, year,
                 entry_types_id, editor=None, series=None, type=None,
                 chapter=None, pages=None, address=None, edition=None,
                 month=None, note=None, volume=None, number=None):
        self.author = author
        self.title = title
        self.booktitle = booktitle
        self.publisher = publisher
        self.year = year
        self.entry_types_id = entry_types_id
        self.editor = editor
        self.series = series
        self.type = type
        self.chapter = chapter
        self.pages = pages
        self.address = address
        self.edition = edition
        self.month = month
        self.note = note
        self.volume = volume
        self.number = number

    def save(self, session):
        entry = ref.Entry(author=self.author, title=self.title,
                          booktitle=self.booktitle, publisher=self.publisher,
                          year=self.year, entry_types_id=self.entry_types_id,
                          editor=self.editor, series=self.series,
                          type=self.type, chapter=self.chapter,
                          pages=self.pages, address=self.address,
                          edition=self.edition, month=self.month,
                          note=self.note, volume=self.volume,
                          number=self.number)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'author': self.author, 'title': self.title,
             'booktitle': self.booktitle, 'publisher': self.publisher,
             'year': self.year, 'entry_types_id': self.entry_types_id,
             'editor': self.editor, 'series': self.series, 'type': self.type,
             'chapter': self.chapter, 'pages': self.pages,
             'address': self.address, 'edition': self.edition,
             'month': self.month, 'note': self.note, 'volume': self.volume,
             'number': self.number})


class InproceedingsForm:
    def __init__(self, author, title, booktitle, year, entry_types_id,
                 editor=None, series=None, pages=None, address=None, month=None,
                 organization=None, publisher=None, note=None, volume=None,
                 number=None):
        self.author = author
        self.title = title
        self.booktitle = booktitle
        self.year = year
        self.entry_types_id = entry_types_id
        self.editor = editor
        self.series = series
        self.pages = pages
        self.address = address
        self.month = month
        self.organization = organization
        self.publisher = publisher
        self.note = note
        self.volume = volume
        self.number = number

    def save(self, session):
        entry = ref.Entry(author=self.author, title=self.title,
                          booktitle=self.booktitle, year=self.year,
                          entry_types_id=self.entry_types_id,
                          editor=self.editor, series=self.series,
                          pages=self.pages, address=self.address,
                          month=self.month, organization=self.organization,
                          publisher=self.publisher, note=self.note,
                          volume=self.volume, number=self.number)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'author': self.author, 'title': self.title,
             'booktitle': self.booktitle, 'year': self.year,
             'entry_types_id': self.entry_types_id, 'editor': self.editor,
             'series': self.series, 'pages': self.pages,
             'address': self.address, 'month': self.month,
             'organization': self.organization, 'publisher': self.publisher,
             'note': self.note, 'volume': self.volume, 'number': self.number})


class ManualForm:
    def __init__(self, address, title, year, entry_types_id, author=None,
                 organization=None, edition=None, month=None, note=None):
        self.address = address
        self.title = title
        self.year = year
        self.entry_types_id = entry_types_id
        self.author = author
        self.organization = organization
        self.edition = edition
        self.month = month
        self.note = note

    def save(self, session):
        entry = ref.Entry(address=self.address, title=self.title,
                          year=self.year, entry_types_id=self.entry_types_id,
                          author=self.author, organization=self.organization,
                          edition=self.edition, month=self.month,
                          note=self.note)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'address': self.address, 'title': self.title, 'year': self.year,
             'entry_types_id': self.entry_types_id, 'author': self.author,
             'organization': self.organization, 'edition': self.edition,
             'month': self.month, 'note': self.note})


class MastersthesisForm:
    def __init__(self, author, title, school, year, entry_types_id, type=None,
                 address=None, month=None, note=None):
        self.author = author
        self.title = title
        self.school = school
        self.year = year
        self.entry_types_id = entry_types_id
        self.type = type
        self.address = address
        self.month = month
        self.note = note

    def save(self, session):
        entry = ref.Entry(author=self.author, title=self.title,
                          school=self.school, year=self.year,
                          entry_types_id=self.entry_types_id, type=self.type,
                          address=self.address, month=self.month,
                          note=self.note)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'author': self.author, 'title': self.title, 'school': self.school,
             'year': self.year, 'entry_types_id': self.entry_types_id,
             'type': self.type, 'address': self.address, 'month': self.month,
             'note': self.note})


class MiscForm:
    def __init__(self, entry_types_id, author=None, title=None,
                 howpublished=None, month=None, year=None, note=None):
        self.entry_types_id = entry_types_id
        self.author = author
        self.title = title
        self.howpublished = howpublished
        self.month = month
        self.year = year
        self.note = note

    def save(self, session):
        entry = ref.Entry(entry_types_id=self.entry_types_id,
                          author=self.author, title=self.title,
                          howpublished=self.howpublished, month=self.month,
                          year=self.year, note=self.note)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'entry_types_id': self.entry_types_id, 'author': self.author,
             'title': self.title, 'howpublished': self.howpublished,
             'month': self.month, 'year': self.year, 'note': self.note})


class PhdthesisForm:
    def __init__(self, author, title, school, year, entry_types_id, type=None,
                 address=None, month=None, note=None):
        self.author = author
        self.title = title
        self.school = school
        self.year = year
        self.entry_types_id = entry_types_id
        self.type = type
        self.address = address
        self.month = month
        self.note = note

    def save(self, session):
        entry = ref.Entry(author=self.author, title=self.title,
                          school=self.school, year=self.year,
                          entry_types_id=self.entry_types_id, type=self.type,
                          address=self.address, month=self.month,
                          note=self.note)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'author': self.author, 'title': self.title, 'school': self.school,
             'year': self.year, 'entry_types_id': self.entry_types_id,
             'type': self.type, 'address': self.address, 'month': self.month,
             'note': self.note})


class ProceedingsForm:
    def __init__(self, title, year, entry_types_id, editor=None, series=None,
                 address=None, month=None, organization=None, publisher=None,
                 note=None, volume=None, number=None):
        self.title = title
        self.year = year
        self.entry_types_id = entry_types_id
        self.editor = editor
        self.series = series
        self.address = address
        self.month = month
        self.organization = organization
        self.publisher = publisher
        self.note = note
        self.volume = volume
        self.number = number

    def save(self, session):
        entry = ref.Entry(title=self.title, year=self.year,
                          entry_types_id=self.entry_types_id,
                          editor=self.editor, series=self.series,
                          address=self.address, month=self.month,
                          organization=self.organization,
                          publisher=self.publisher, note=self.note,
                          volume=self.volume, number=self.number)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'title': self.title, 'year': self.year,
             'entry_types_id': self.entry_types_id, 'editor': self.editor,
             'series': self.series, 'address': self.address,
             'month': self.month, 'organization': self.organization,
             'publisher': self.publisher, 'note': self.note,
             'volume': self.volume, 'number': self.number})


class TechreportForm:
    def __init__(self, author, title, institution, year, entry_types_id,
                 type=None, note=None, number=None, address=None, month=None):
        self.author = author
        self.title = title
        self.institution = institution
        self.year = year
        self.entry_types_id = entry_types_id
        self.type = type
        self.note = note
        self.number = number
        self.address = address
        self.month = month

    def save(self, session):
        entry = ref.Entry(author=self.author, title=self.title,
                          institution=self.institution, year=self.year,
                          entry_types_id=self.entry_types_id, type=self.type,
                          note=self.note, number=self.number,
                          address=self.address, month=self.month)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'author': self.author, 'title': self.title,
             'institution': self.institution, 'year': self.year,
             'entry_types_id': self.entry_types_id, 'type': self.type,
             'note': self.note, 'number': self.number, 'address': self.address,
             'month': self.month})


class UnpublishedForm:
    def __init__(self, author, title, note, entry_types_id, month=None,
                 year=None):
        self.author = author
        self.title = title
        self.note = note
        self.entry_types_id = entry_types_id
        self.month = month
        self.year = year

    def save(self, session):
        entry = ref.Entry(author=self.author, title=self.title, note=self.note,
                          entry_types_id=self.entry_types_id, month=self.month,
                          year=self.year)
        session.add(entry)

    def edit(self, session, entries_id):
        session.query(ref.Entry).filter(
            ref.Entry.entries_id == entries_id).update(
            {'author': self.author, 'title': self.title, 'note': self.note,
             'entry_types_id': self.entry_types_id, 'month': self.month,
             'year': self.year})
