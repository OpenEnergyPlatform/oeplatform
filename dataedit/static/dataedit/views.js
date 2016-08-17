function render_generic_field(value, field, record){
    value = field.defaultRenderers[field.get('type')](value, field, record);
    if(record.comment != '' && !isNaN(record.comment)){
        value = '<div style="padding:0px; margin:0px; background-color:FF0000">' + value + '</div>'
    }
    return value;
}

function render_comment(value, field, record){
    if(value){
        return (
    "<div style='position:absolute'>"
        + "<a class='glyphicon glyphicon-info-sign' data-toggle='modal' data-target='#myModal" + record.id + "'></a>"
        + "<div id='myModal" + record.id + "' class='modal' role='dialog' data-backdrop='false' style='top:100px; width:30%;z-index:0;'>"
            + "<div class='modal-content'>"
                + "<div class='modal-header'>"
                    + "<button type='button' class='close' data-dismiss='modal'>&times;</button>"
                    + "<h4 class='modal-title'>Metadata</h4>"
                + "</div>"
                + "<div class='modal-body'>"
                    + "<table>"
                        + "<tr>"
                            + "<th>Method:</th>"
                            + "<td>" + value.method + "</td>"
                        + "</tr>"
                        + "<tr>"
                            + "<th>Origin:</th>"
                            + "<td>" + value.origin + "</td>"
                        + "</tr>"
                    + "</table>"
                + "</div>"
            + "</div>"
        + "</div>"
    + "</div>");
    }
    else{
        return ""
    }
}