from egoio.db_tables import references as ref
from sqlalchemy.orm import relationship, Session
from django.shortcuts import render, redirect
from sqlalchemy import create_engine, MetaData
import bibtexparser as btp
from api.actions import _get_engine
from django.views.generic import View
import datetime
from literature import forms


# Create your views here.


def list_references(request):
    engine = _get_engine()
    sess = Session(bind=engine)
    refs = [r for r in sess.query(ref.Entry)]
    return render(request, 'literature/list_references.html', {'refs': refs})


def show_entry(request, entries_id):
    engine = _get_engine()
    sess = Session(bind=engine)
    entry = sess.query(ref.Entry).filter(
        ref.Entry.entries_id == entries_id).first()
    return render(request, 'literature/reference.html', {'entry': entry})


FORM_MAP = {'article': forms.ArticleForm,
            'book': forms.BookForm,
            'booklet': forms.BookletForm,
            'conference': forms.ConferenceForm,
            'inbook': forms.InbookForm,
            'incollection': forms.IncollectionForm,
            'inproceedings': forms.InproceedingsForm,
            'manual': forms.ManualForm,
            'mastersthesis': forms.MastersthesisForm,
            'misc': forms.MiscForm,
            'phdthesis': forms.PhdthesisForm,
            'proceedings': forms.ProceedingsForm,
            'techreport': forms.TechreportForm,
            'unpublished': forms.UnpublishedForm}


class LiteratureView(View):
    def get(self, request, entries_id=None):
        if entries_id:
            engine = _get_engine()
            sess = Session(bind=engine)
            entry = sess.query(ref.Entry).filter(ref.Entry.entries_id == entries_id).first()
            btype = entry.entry_types.label if entry.entry_types else 'article'
        else:
            entry = ref.Entry()
            btype = None
        return render(request, 'literature/reference_form.html',
                      {'entry': entry,
                       'years': range(datetime.datetime.now().year, 1899, -1),
                       'id': entries_id, 'btype': btype}, )

    def post(self, request, entries_id=None):

        # I do not know why this is necessary, but it is :/
        data = {k: v for k, v in request.POST.items()}
        del data['csrfmiddlewaretoken']

        engine = _get_engine()
        metadata = MetaData()
        metadata.create_all(bind=engine)
        sess = Session(bind=engine)
        bibtype = data.pop('bibtype')
        entry_type = get_bibtype_id(bibtype)

        if 'edit' in data:
            entries_id = data['edit']
            del data['edit']

        # TODO: Remove if clause after rigorous testing
        data['entry_types_id'] = entry_type.entry_types_id if entry_type else 1
        form = FORM_MAP[bibtype](**data)

        if entries_id:
            form.edit(sess,entries_id)
        else:
            form.save(sess)

        sess.commit()
        return redirect('/literature')


def get_bibtype_id(bibtype):
    engine = _get_engine()
    sess = Session(bind=engine)
    return sess.query(ref.EntryType).filter(
        ref.EntryType.label == bibtype).first()


def read_bibtexfile(file_name):
    engine = _get_engine()
    metadata = MetaData()
    metadata.create_all(bind=engine)
    sess = Session(bind=engine)

    with open(file_name) as bibtex_file:
        bibtex_database = btp.load(bibtex_file)
    for ent in bibtex_database.entries:
        props = {k.name: ent[k.name.replace('entries.', '')] for k in
                 ref.Entry.__table__.c if k.name.replace('entries.', '') in ent}
        en = ref.Entry(**props)
        sess.add(en)
    sess.commit()
