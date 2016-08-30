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

function plot_view(dataset, editable, div, record){


        var createMultiView = function(dataset, state) {
            // remove existing multiview if present
            var reload = false;
            if (record.multiView) {

                record.multiView.remove();
                record.multiView = null;
                reload = true;
                record.explorerDiv.contents().remove();
            }

            var $el = $('<div />');
            $el.appendTo(record.explorerDiv);

            var state = {
                                gridOptions: {
                                    editable: editable,
                                    enableAddRow: false//editable,
                                },
                            };

            if(editable)
            {
                state.columnsEditor = dataset.fields.map(function(field){
                                    return {column: field.id, editor: field.editor};
                                })
            }

            var grid = new recline.View.SlickGrid({
                            model: dataset,
                            state: state
            });

            /*grid.onAddNewRow.subscribe(function (e, args) {
              var item = args.item;
              grid.invalidateRow(data.length);
              data.push(item);
              grid.updateRowCount();
              grid.render();
            });*/

            old_length = dataset.records.length;
            dataset.records.on('add',function(record){
              equal(dataset.records.length ,old_length + 1 );
            });




            var views = [
                {
                        view: grid,
                        label: 'Grid',
                        id: 'Grid',
                },
                    {
                        view: new recline.View.Map({model: dataset}),
                        label: 'Map',
                        id: 'map'
                    },
                    {
                        view: new recline.View.Graph({model: dataset}),
                        label: 'Graph',
                        id: 'graph'
                    },
            ];



            var multiView = new recline.View.MultiView({
                model: dataset,
                el: $el,
                state: state,
                views: views
            });
            return multiView;
        }

        jQuery(function($) {
            record.explorerDiv = div;
            record.multiView = createMultiView(dataset);

        });
}