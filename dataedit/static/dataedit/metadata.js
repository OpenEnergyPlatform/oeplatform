
function create_box($parent, id){
    var $container = $('<div class="metacontainer" id='+id+'></div>');

    var $header = $('<div class="metacontainer-header"></div>')

    var $removeBtn = $('<a style="color:white" onclick="$(\'#'+id+'\').remove();"><span class="glyphicon glyphicon-minus-sign"/></a>');
    var $subcontainer = $('<div class="metaformframe" id='+id+'></div>')

    $header.append($removeBtn);
    $container.append($header);
    $container.append($subcontainer);
    $parent.append($container);
    return $subcontainer
}

function add_labeled_textfield($container, label, id, value){
    var $input_label = $('<label for="' + id + '">'+label+'</label>');
    var $input = $('<input autocomplete="off" class="input form-control" id="' + id + '" name="' + id + '" type="text" value="' + value + '">');
    $container.append($input_label);
    $container.append($input);
}

function add_language($parent, obj){
    prefix = 'language';
    const idx = $parent[0].childElementCount;
    const label=format_label(prefix, idx);
    var $container = create_box($parent, prefix+idx);

    if('undefined' === typeof obj){
        var obj={};
        obj.language='';
    }

    add_labeled_textfield($container, label, prefix+idx, obj.language);
};

function add_keywords($parent, obj){
    prefix='keywords';
    const idx = $parent[0].childElementCount;
    console.log(idx);
    const label = format_label(prefix, idx);
    var $container = create_box($parent, prefix+idx);

    if('undefined' === typeof obj){
        var obj={};
        obj.keywords='';
    }

    add_labeled_textfield($container, label, prefix+idx, obj.keywords);
};

function add_sources($parent, obj){
    prefix='sources';
    indexes[prefix] = indexes[prefix] +1;
    var $container = create_box($parent);

    if('undefined' === typeof obj){
        var obj={};
        obj.name='';
        obj.description='';
        obj.url='';
        obj.license='';
        obj.copyright='';
    }

    add_labeled_textfield($container, 'Name', prefix+indexes[prefix]+'_name', obj.name);
    add_labeled_textfield($container, 'Description', prefix+indexes[prefix]+'_description', obj.description);
    add_labeled_textfield($container, 'URL', prefix+indexes[prefix]+'_url', obj.url);
    add_labeled_textfield($container, 'License', prefix+indexes[prefix]+'_license', obj.license);
    add_labeled_textfield($container, 'Copyright', prefix+indexes[prefix]+'_copyright', obj.copyright);
};

function add_license($parent, obj){
    prefix='license';
    indexes[prefix] = indexes[prefix] +1;
    var $container = create_box($parent);

    if('undefined' === typeof obj){
        var obj={};
        obj.id='';
        obj.name='';
        obj.version='';
        obj.url='';
        obj.instruction='';
        obj.copyright='';
    }

    add_labeled_textfield($container, 'ID', prefix+indexes[prefix]+'_id', obj.id);
    add_labeled_textfield($container, 'Name', prefix+indexes[prefix]+'_name', obj.name);
    add_labeled_textfield($container, 'Version', prefix+indexes[prefix]+'_version', obj.version);
    add_labeled_textfield($container, 'URL', prefix+indexes[prefix]+'_url', obj.url);
    add_labeled_textfield($container, 'Instruction', prefix+indexes[prefix]+'_instruction', obj.instruction);
    add_labeled_textfield($container, 'Copyright', prefix+indexes[prefix]+'_copyright', obj.copyright);
};

function add_contributors($parent, obj){
    prefix='contributors';
    indexes[prefix] = indexes[prefix] +1;
    var $container = create_box($parent);;

    if('undefined' === typeof obj){
        var obj={};
        obj.name='';
        obj.email='';
        obj.date='';
        obj.comment='';
    }

    add_labeled_textfield($container, 'Name', prefix+indexes[prefix]+'_name', obj.name);
    add_labeled_textfield($container, 'E-Mail', prefix+indexes[prefix]+'_email', obj.email);
    add_labeled_textfield($container, 'Date', prefix+indexes[prefix]+'_date', obj.date);
    add_labeled_textfield($container, 'Comment', prefix+indexes[prefix]+'_comment', obj.comment);
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