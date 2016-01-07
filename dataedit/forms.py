from django import forms
from django.db import models

# This structure maps postgresql data types to django forms
typemap = [
    (["smallint"], models.SmallIntegerField),
    (["integer","serial"], forms.IntegerField),
    (["bigint","bigserial"], models.BigIntegerField),
    (["decimal","numeric","real","double precision","money"]
        ,models.DecimalField),
    (["character varying(","varying(", 
        "varchar(", "character(","char(","text"], forms.CharField),
    (["timestamp","date", "time"], forms.DateTimeField),
    (["bytea"],forms.CharField),
    (["interval"],models.DurationField),
    (["boolean"],models.BooleanField),
    (["point","line","lseg","box","path","polygon","circle"]
        ,forms.CharField),
    (["cidr","inet","macaddr"],forms.CharField),
    (["bit(", "bit varying("],forms.CharField),
    (["uuid"],models.UUIDField),
    (["xml"],forms.CharField)]
#TODO:  add missing types: Textsearch, Enumeration, \
#       Composite types, Object Identifier Types, Pseudo-Types

def type2field(typename: str):
    additionals = {}    
    resField = None
    typename = typename.lower()
    for (keyList,field) in typemap:
        if any(typename.startswith(key) for key in keyList):
            resField = field
    if "[" in typename:
        return resField
    if not resField:
        raise Exception("type '{0}' does not \
translate to a django field".format(typename))
    
    for _ in range(typename.count("[")-1):
        resField = ArrayField(resField())    
    if "[" in typename:
        resField = lambda **x : ArrayField(resField(),**x) 

    return resField  
    
class InputForm(forms.Form):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields")
        super(forms.Form, self).__init__(*args, **kwargs)
        for (name, typename) in fields:
            self.fields[name] = type2field(typename)(label=name)


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()

class UploadMapForm(forms.Form):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields")
        headers = kwargs.pop("headers")
        super(forms.Form, self).__init__(*args, **kwargs)
        print(headers)
        for (name, typename) in fields:
            self.fields[name] = forms.ChoiceField(label=name, choices=((x,x) for x in headers))
