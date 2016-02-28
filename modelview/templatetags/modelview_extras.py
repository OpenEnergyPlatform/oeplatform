from django import template
import matplotlib.pyplot as plt
import urllib3
import json
import datetime
from scipy import stats
import numpy 

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

@register.simple_tag
def get_field_attr(instance, field_name, attr):
    """
    Returns verbose_name for a field.
    """
    return instance._meta.get_field(field_name).__dict__[attr]
    
@register.assignment_tag
def assign_field_attr(instance, field_name, attr):
    """
    Returns verbose_name for a field.
    """
    return instance._meta.get_field(field_name).__dict__[attr]

@register.filter('fieldtype')
def fieldtype(field):
    return field.field.widget.__class__.__name__

