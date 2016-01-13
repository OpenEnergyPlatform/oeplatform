from django import template
register = template.Library()

@register.simple_tag
def checktable(model, label, prefixes ,suffixes, rowlabels=""):
    rls = rowlabels.split(";") 
       
    header = "<td></td>" if rls != [""] else ""
    data = ""
    print(model.__dict__)
    for s in suffixes.split(";"):    
        header += '<td>{0}</td>'.format(s)  
    i = 0
    
    for prefix in prefixes.split(";"):
        if rls != [""]:
            data += "<tr> <td> {0} </td>".format(rls[i])
            i+=1
        else:
            data += "<tr>"
        for s in suffixes.split(";"):    
            if model.__dict__["{0}_{1}".format(prefix,s)]:
                data +=  '<td align="center"> <span class="glyphicon glyphicon-ok"></span> </td>'
            else:
                data +=  '<td align="center"> <span class="glyphicon glyphicon-remove"></span> </td>'
        data += "</tr>"
    return"""<tr>
                <td valign="top"  class="rowlabel"> {0}</td>
                <td> 
                    <table  class="table table-bordered" style="table-layout: fixed;">
                        <tr>
                            {1}
                        </tr>
                        {2}
                    </table>
                </td>
            </tr>""".format(label,header,data)
