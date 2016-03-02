from django import template
import matplotlib.pyplot as plt
import urllib3
import json
import datetime
from scipy import stats
import numpy 
from django.utils.safestring import mark_safe
from django.utils.html import format_html
register = template.Library()

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
    for name in labels.split(","):
        decider = name
        text = name 
        if "=" in name:
            decider,text = name.split("=")
        
        if model.__dict__[decider]:
            if first:
                first=False
            else:
                s+=", "
            s+= model.__dict__[text]
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
    return format_html("<tr><td class='sheetlabel'>{label}</td><td>{s}</td></tr>".format(label=model._meta.get_field(label+"_kind").verbose_name, s=s))

@register.simple_tag
def get_verbose_field_name(instance, field_name):
    """
    Returns verbose_name for a field.
    """
    return instance._meta.get_field(field_name).verbose_name

@register.simple_tag
def get_field(instance, field_name):
    """
    Returns verbose_name for a field.
    """
    return instance.__dict__[field_name]

@register.assignment_tag
def assign_field(instance, field_name):
    """
    Returns verbose_name for a field.
    """
    return instance.__dict__[field_name]


@register.simple_tag
def get_field_attr(instance, field_name, attr, cut=None):
    """
    Returns verbose_name for a field.
    """
    val = instance._meta.get_field(field_name).__dict__[attr]
    if cut:
        val = val.replace(cut,"")
    return val
    
@register.assignment_tag
def assign_field_attr(instance, field_name, attr):
    """
    Returns verbose_name for a field.
    """
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
