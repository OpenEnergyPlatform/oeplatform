import datetime
import io

import bibtexparser as btp
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import View
from egoio.db_tables import reference as ref
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, relationship

from api.actions import _get_engine
from literature import forms

# Create your views here.


def list_references(request, error=None):
    engine = _get_engine()
    sess = Session(bind=engine)
    refs = sorted((r for r in sess.query(ref.Entry)), key=lambda r: r.title)
    return render(
        request, "literature/list_references.html", {"refs": refs, "error": error}
    )


def show_entry(request, entries_id):
    engine = _get_engine()
    sess = Session(bind=engine)
    entry = sess.query(ref.Entry).filter(ref.Entry.entries_id == entries_id).first()
    return render(request, "literature/reference.html", {"entry": entry})


FORM_MAP = {
    "article": forms.ArticleForm,
    "book": forms.BookForm,
    "booklet": forms.BookletForm,
    "conference": forms.ConferenceForm,
    "inbook": forms.InbookForm,
    "incollection": forms.IncollectionForm,
    "inproceedings": forms.InproceedingsForm,
    "manual": forms.ManualForm,
    "mastersthesis": forms.MastersthesisForm,
    "misc": forms.MiscForm,
    "phdthesis": forms.PhdthesisForm,
    "proceedings": forms.ProceedingsForm,
    "techreport": forms.TechreportForm,
    "unpublished": forms.UnpublishedForm,
}


class LiteratureView(LoginRequiredMixin, View):
    def get(self, request, entries_id=None):
        if entries_id:
            engine = _get_engine()
            sess = Session(bind=engine)
            entry = (
                sess.query(ref.Entry).filter(ref.Entry.entries_id == entries_id).first()
            )
            btype = entry.entry_types.label if entry.entry_types else "article"
        else:
            entry = ref.Entry()
            btype = None
        return render(
            request,
            "literature/reference_form.html",
            {
                "entry": entry,
                "years": range(datetime.datetime.now().year, 1899, -1),
                "id": entries_id,
                "btype": btype,
            },
        )

    def post(self, request, entries_id=None):

        # I do not know why this is necessary, but it is :/
        data = {k: v for k, v in request.POST.items()}
        del data["csrfmiddlewaretoken"]

        engine = _get_engine()
        metadata = MetaData()
        metadata.create_all(bind=engine)
        sess = Session(bind=engine)
        bibtype = data.pop("bibtype")
        entry_type = get_bibtype_id(bibtype)

        if "edit" in data:
            entries_id = data["edit"]
            del data["edit"]

        # TODO: Remove if clause after rigorous testing
        data["entry_types_id"] = entry_type.entry_types_id if entry_type else 1
        form = FORM_MAP[bibtype](**data)

        if entries_id:
            form.edit(sess, entries_id)
        else:
            form.save(sess)

        sess.commit()
        return redirect("/literature")


@login_required(login_url="/login/")
def upload(request):
    file = request.FILES["bibtex"]
    try:
        return read_bibtexfile(io.TextIOWrapper(file.file))
    except:
        return list_references(request, "Not a valid bibtex file!")


def get_bibtype_id(bibtype):
    engine = _get_engine()
    sess = Session(bind=engine)
    et = sess.query(ref.EntryType).filter(ref.EntryType.label == bibtype).first()
    sess.close()
    return et


def read_bibtexfile(bibtex_file):
    engine = _get_engine()
    metadata = MetaData()
    metadata.create_all(bind=engine)
    sess = Session(bind=engine)

    bibtex_database = btp.load(bibtex_file)
    for ent in bibtex_database.entries:
        props = {
            k.name: ent[k.name.replace("entries.", "")]
            for k in ref.Entry.__table__.c
            if k.name.replace("entries.", "") in ent
        }
        props["entry_types_id"] = get_bibtype_id(ent["ENTRYTYPE"])

        en = ref.Entry(**props)
        sess.add(en)
    sess.commit()
    sess.close()
    return redirect("/literature")
