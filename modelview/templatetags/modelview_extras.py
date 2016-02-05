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


