indexes = {
'sources':0,
'spatial':0,
'license':0,
'contributors':0,
'resources':[],
};

function create_box($parent){
    var $container = $('<div class="metacontainer" id='+prefix+indexes[prefix]+'></div>');

    var $header = $('<div class="metacontainer-header"></div>')

    var $removeBtn = $('<a style="color:white" onclick="$(\'#'+prefix+indexes[prefix]+'\').remove();"><span class="glyphicon glyphicon-minus-sign"/></a>');
    var $container = $('<div class="metaformframe" id='+prefix+indexes[prefix]+'></div>')

    $header.append($removeBtn);
    $container.append($header);
    $container.append($container);
    $parent.append($container);
    return $container
}

function add_labeled_textfield($container, label, id){
    var $input_label = $('<label for="' + id + '">'+label+'</label>');
    var $input = $('<input autocomplete="off" class="input form-control" id="' + id + '" name="' + id + '" type="text">');
    $container.append($input_label);
    $container.append($input);
}

function add_source($parent){
    prefix='source';
    indexes[prefix] = indexes[prefix] +1;
    var $container = create_box($parent);
    add_labeled_textfield($container, 'Description', prefix+indexes[prefix]+'_description');
    add_labeled_textfield($container, 'URL', prefix+indexes[prefix]+'_url');
    add_labeled_textfield($container, 'License', prefix+indexes[prefix]+'_license');
    add_labeled_textfield($container, 'Copyright', prefix+indexes[prefix]+'_copyright');
};

function add_spatial($parent){
    prefix='source';
    indexes[prefix] = indexes[prefix] +1;
    var $container = create_box($parent);;
    add_labeled_textfield($container, 'Extend', prefix+indexes[prefix]+'_extend');
    add_labeled_textfield($container, 'Resolution', prefix+indexes[prefix]+'_Resolution');
};

function add_license($parent){
    prefix='license';
    indexes[prefix] = indexes[prefix] +1;
    var $container = create_box($parent);;
    add_labeled_textfield($container, 'ID', prefix+indexes[prefix]+'_id');
    add_labeled_textfield($container, 'Name', prefix+indexes[prefix]+'_name');
    add_labeled_textfield($container, 'Version', prefix+indexes[prefix]+'_version');
    add_labeled_textfield($container, 'URL', prefix+indexes[prefix]+'_url');
    add_labeled_textfield($container, 'Instruction', prefix+indexes[prefix]+'_instruction');
    add_labeled_textfield($container, 'Copyright', prefix+indexes[prefix]+'_copyright');
};

function add_contributors($parent){
    prefix='license';
    indexes[prefix] = indexes[prefix] +1;
    var $container = create_box($parent);;
    add_labeled_textfield($container, 'Name', prefix+indexes[prefix]+'_name');
    add_labeled_textfield($container, 'E-Mail', prefix+indexes[prefix]+'_email');
    add_labeled_textfield($container, 'Date', prefix+indexes[prefix]+'_date');
    add_labeled_textfield($container, 'Comment', prefix+indexes[prefix]+'_comment');
};

function add_resources($parent){
    prefix='license';
    indexes[prefix] = indexes[prefix] +1;
    var $container = create_box($parent);;
    add_labeled_textfield($container, 'Name', prefix+indexes[prefix]+'_name');
    add_labeled_textfield($container, 'E-Mail', prefix+indexes[prefix]+'_email');
    add_labeled_textfield($container, 'Date', prefix+indexes[prefix]+'_date');
    add_labeled_textfield($container, 'Comment', prefix+indexes[prefix]+'_comment');
};

function add_list_field(id){
    var index = window[id+"_counter"];
    var $div = $('<div id="'+id+'_wrapper_'+index+'"> \
        <table  style="width:100%"><tr><td class="form-group"> <input class="form-control" name="'+id+'_'+index+'" id="'+id+'_'+index+'"/></td> \
        <td><a style="position:inline" onclick="$(\'#'+id+'_wrapper_'+index+'\').remove();"><span class="glyphicon glyphicon-minus-sign"/></a></td></tr></table> \
    </div>');
    $div.appendTo($('#'+id+'_container'));
    window[id+"_counter"] += 1;
    add_source($div);
};

function add_url_list_field(id){
    var index = window[id+"_counter"];
    var $div = $('<div id="'+id+'_wrapper_'+index+'"> \
        <div class="form-group"> \
            <label>Name</label> \
            <input class="form-control" name="'+id+'_name_'+index+'"/> \
        </div> \
        <div class="form-group"> \
            <label>URL</label> \
            <input class="form-control" name="'+id+'_url_'+index+'"/> \
        </div> \
        <a onclick="$(\'#'+id+'_wrapper_'+index+'\').remove();"><span class="glyphicon glyphicon-minus-sign"/></a><hr> \
    </div>');
    $div.appendTo($('#'+id+'_container'));
    window[id+"_counter"] += 1;
};