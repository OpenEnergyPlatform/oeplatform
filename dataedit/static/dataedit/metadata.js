function format_label(s){
  if (typeof s !== 'string') return ''
  s = s.split('_').pop()
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function extract_el_index(name){
    // get the number at the end of the name
  	name = name.split('_').pop()
	return name.match(/\d+/)[0]
}


function remove_element(parent){
    var idx = extract_el_index(parent)
    parent = parent.substring(0, parent.length - idx.length);

    //find element container
    var $parent = $('#' + parent + '_container');
    // if element is not the last, proceed to removal
    if($parent[0].childElementCount > 1){
        var $container = $('#'+ parent + idx);
        $container.remove();
    }
}


function add_list_objects(prefix){

    var $parent = $('#' + prefix + '_container')

    // create index of the new element in the list for the ids of child elements
    // of the new element
    const idx = parseInt(extract_el_index($parent[0].lastChild.id)) + 1;

    const label = format_label(prefix);

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


    var clone_idx = extract_el_index($clone.id);
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