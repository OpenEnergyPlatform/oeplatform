function format_label(s){
  if (typeof s !== 'string') return ''
  s = s.split('_').pop()
  return s.charAt(0).toUpperCase() + s.slice(1)
}

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

function add_list_objects(prefix){

    var $parent = $('#' + prefix + '_container')

    // create index of the new element in the list for the ids of child elements
    // of the new element
    const idx = parseInt($parent[0].lastChild.id.match(/\d+/)[0]) + 1;

    const label=format_label(prefix);

    // copy the first element (so that the id will always bear the index 0
    var $clone = $parent[0].firstElementChild.cloneNode(true);


    // fetch the fields of the element which are lists themselves
    var sub_container = $clone.querySelectorAll('[id*=_container]');
    for (let i = 0; i < sub_container.length; i++){
        // empty the list of all but the first element
        while (sub_container[i].childNodes.length > 1) {
            sub_container[i].removeChild(sub_container[i].lastChild);
        }
    }

    var clone_idx = $clone.id.match(/\d+/)[0];
    // replace the new index in the ids of the clone's children elements
    var new_id = $clone.id;
    $clone.id = new_id.replace(prefix + clone_idx, prefix + idx);

    var elements = $clone.querySelectorAll('[id*=' + prefix + clone_idx + ']');
    for (let i = 0; i < elements.length; i++) {
        // replace the copied element id's
        new_id = elements[i].id;
        elements[i].id = new_id.replace(prefix + clone_idx, prefix + idx);
        if (elements[i].tagName === 'INPUT') {
            // clear the input fields
            elements[i].value="";
            elements[i].name = new_id.replace(prefix + clone_idx, prefix + idx);
        }
    }

    elements = $clone.querySelectorAll("label");
    for (let i = 0; i < elements.length; i++) {
        // replace the copied labels 'for' attribute
        elements[i].htmlFor = elements[i].htmlFor.replace(prefix + clone_idx, prefix + idx);
        // replace the copied labels' content
        if(elements[i].innerHTML.includes(label + ' ' + clone_idx)){
            elements[i].innerHTML = label + ' ' + idx;
        }
    }

    elements = $clone.querySelectorAll("a");
    for (let i = 0; i < elements.length; i++) {
        // replace the copied links' (a) onclick' attribute
        new_id = elements[i].attributes['onclick'].value.replace(prefix + clone_idx, prefix + idx);
        elements[i].attributes['onclick'].value = new_id;
    }

    $parent.append($clone)
};
function add_sources($parent, obj){
    prefix='sources';
    const idx = $parent[0].childElementCount;
    const label=format_label(prefix, idx);

    var $clone = $parent[0].firstElementChild.cloneNode(true);

    // fetch the fields which are list
    var sub_container = $clone.querySelectorAll('[id*=_container]');
    for (let i = 0; i < sub_container.length; i++){

        while (sub_container[i].childNodes.length > 1) {
            sub_container[i].removeChild(sub_container[i].lastChild);
        }
    }

    $clone.id = prefix+idx;
    var elements = $clone.querySelectorAll('[id*='+prefix+'0]');
    console.log(elements);

    for (let i = 0; i < elements.length; i++) {

        // replace the copied element id's
        var new_id = elements[i].id;
        elements[i].id = new_id.replace(prefix+'0', prefix+idx);
        if (elements[i].tagName === 'INPUT') {
        // clear the input fields
            console.log(elements[i]);
            elements[i].value="";
            elements[i].name = new_id.replace(prefix+'0', prefix+idx);
        }
    }

    $parent.append($clone)
};

function add_licenses($parent, obj){
    prefix='licenses';
    const idx = $parent[0].childElementCount;
    const label=format_label(prefix, idx);

    var $clone = $parent[0].firstElementChild.cloneNode(true);

    $clone.id= prefix+idx;
    $clone.querySelectorAll('[id*='+prefix+'0]').forEach(function(element){
        // replace the copied element id's
        var new_id = element.id;
        element.id = new_id.replace(prefix+'0', prefix+idx);
        if (element.tagName === 'INPUT') {
        // clear the input fields
            element.value="";
            element.name = new_id.replace(prefix+'0', prefix+idx);
            console.log(element);
        }

    });

    $parent.append($clone)
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