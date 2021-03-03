from django.forms.widgets import TextInput
from django.utils.html import format_html, format_html_join, mark_safe
from typing import Type

from modelview.rdf import handler


class Field(handler.Rederable):
    _handler = handler.DefaultHandler
    _widged = TextInput

    def __init__(
        self,
        rdf_name,
        verbose_name=None,
        handler: handler.Handler = None,
        help_text: str = None,
    ):
        self.rdf_name = rdf_name
        self.verbose_name = verbose_name
        self.handler = handler if handler else self._handler()
        self.values = None
        self.help_text = help_text

    def to_triples(self, subject):
        if self.values is not None:
            for v in self.values:
                yield f"{subject} {self.rdf_name} {v} ."

    def render(self, mode="display", **kwargs):
        it = list(self.values if self.values else ["-"])

        if mode == "display":
            f = self._render_atomic_field
        else:
            f = self._render_atomic_form_field

        vals = [(f(v),) for v in it]

        s = format_html(
            mark_safe(
                '<tr><th><a href="{rdfname}">{vname}</a></th><td>{vals}</td></tr>'
            ),
            rdfname=self.rdf_name,
            vname=self.verbose_name,
            vals=format_html_join(" ", '<li class="list-group-item">{}</li>', vals),
        )
        return s

    def _render_atomic_field(self, obj, **kwargs):
        if isinstance(obj, handler.Rederable):
            return obj.render()
        elif isinstance(obj, list):
            return [self._render_atomic_field(o, **kwargs) for o in obj]
        elif isinstance(obj, str):
            return obj
        elif obj is None:
            return None
        else:
            raise ValueError(obj)

    def _render_atomic_form_field(self, obj, **kwargs):
        if isinstance(obj, handler.Rederable):
            return obj.render()
        elif isinstance(obj, list):
            return [self._render_atomic_form_field(o, **kwargs) for o in obj]
        elif isinstance(obj, str):
            return obj
        else:
            raise ValueError(obj)


class FactoryField(Field):
    def __init__(self, factory, **kwargs):
        self.factory = factory
        super(FactoryField, self).__init__(**kwargs)
