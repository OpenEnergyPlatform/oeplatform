from django import template
import matplotlib.pyplot as plt
import urllib3
import json
import datetime
from scipy import stats
import numpy 
from django.utils.safestring import mark_safe
from django.utils.html import format_html, escape
from django.contrib.postgres.forms.array import SimpleArrayField

register = template.Library()

@register.simple_tag
def prnt(x):
    print(x)

@register.filter
def isArray(field):
    return isinstance(field.field,SimpleArrayField)

@register.filter
def splitarray(field):
    if field.value():
        return field.value().split(",")
    else:
        return None

@register.simple_tag
def checktable(model, label, prefix ,suffixes, separator="_"):      
    header = ""
    data = ""
    for s in suffixes.split(";"):
        if model.__dict__["{0}{2}{1}".format(prefix,s,separator)]:
            data =  '<span class="glyphicon glyphicon-ok"></span>'
        else:
            data =  '<span class="glyphicon glyphicon-remove"></span>'    
        header += '<td>{1} {0} </td>'.format(s,data)  
    i = 0
    return"""<tr>
                <td valign="top"  class="rowlabel"> {0}</td>
                <td> 
                    <table class="profiletable-checktable">
                        <tr>
                            {1}
                        </tr>
                        {2}
                    </table>
                </td>
            </tr>""".format(label,header,"")
            
@register.simple_tag
def checklist(model,labels):
    s = ""
    first = True
    is_other = False
    for name in labels.split(","):
        decider = name
        text = name 
        if "=" in name:
            decider,text = name.split("=")
            is_other = True
        
        if model.__dict__[decider]:
            if first:
                first=False
            else:
                s+=", "
            if is_other:
                s += str(getattr(model, text))
            else:
                s += str(model._meta.get_field(text).verbose_name)
    if s == "":
        s = "-"
    return s

@register.simple_tag
def develop_year(model,label):
    kind = model.__dict__[label+"_kind"]
    if kind == "not estimated":
        s = kind
    else:
        s = "{amount}% {kind} {year}".format(amount=model.__dict__[label+"_amount"],
            kind=kind,
            year=model.__dict__[label+"_year"])
    return format_html("<tr><td class='sheetlabel'>{label}</td><td>{s}</td></tr>".format(label=model._meta.get_field(label+"_amount").verbose_name, s=s))

@register.simple_tag
def get_verbose_field_name(instance, field_name):
    """
    Returns verbose_name for a field.
    """
    return instance._meta.get_field(field_name).verbose_name

@register.simple_tag
def get_field(instance, field_name):
    field = instance.__dict__[field_name]
    if type(field)==list:
        field = ", ".join(field)
    return field


@register.simple_tag
def assign_field(instance, field_name):
    return instance.__dict__[field_name]


@register.filter
def get_model_value(value, arg):
    return stringify(value.__dict__[arg])


def stringify(v):
    if isinstance(v, str):
        parts = v.split(' ')
        max_length = 12
        if len(parts) > max_length:
            parts = parts[:max_length] + ['...']
        v = ' '.join(parts)
        return mark_safe("'%s'"%escape(v.replace('\n','').replace('\r','')))
    elif  isinstance(v, list):
        return mark_safe("[%s]"%(', '.join(map(stringify, v))))
    elif v is None:
        return 'null'
    elif isinstance(v, bool):
        return 'true' if v else 'false'
    return v


@register.filter
def white_out(value, arg):
    return ' '.join(value.split(arg))


@register.simple_tag
def get_field_attr(instance, field_name, attr, cut=None):
    val = instance._meta.get_field(field_name).__dict__[attr]
    if cut:
        val = val.replace(cut,"")
    return val
    
@register.simple_tag
def set_val(val):
    return val    
    
@register.simple_tag
def assign_field_attr(instance, field_name, attr):
    return instance._meta.get_field(field_name).__dict__[attr]

@register.filter('fieldtype')
def fieldtype(field):
    return field.field.widget.__class__.__name__

    
@register.simple_tag
def year_field(instance, field_name):
    field_amount=instance.fields[field_name+'_amount']
    field_kind=instance.fields[field_name+'_kind']
    field_year=instance.fields[field_name+'_year']
    return mark_safe("{{{{ {field}.label }}}}: {{{{ {field}_amount }}}} {{{{ {field}_kind }}}} {{{{ {field}_year }}}} <br>".format(field=field_name))
    
@register.filter
def addEvent(value, arg):
    value.field.widget.attrs[arg] = value.name+"_click(this)"
    return value #value.as_widget(attrs={arg: value.name+"_click(this)"})

@register.simple_tag
def assignClass(field, css):
    class_old = field.field.widget.attrs.get('class', None)
    class_new = class_old + ' ' + css if class_old else css
    field.field.widget.attrs['class'] = class_new
    return field
   
@register.filter
def addClass(value, arg):
    return value.as_widget(attrs={'class': arg})
