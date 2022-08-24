$(".tag-checkbox").on('click', (e) => {
    $(e.target.parentElement).toggleClass("tag-checkbox-checked", e.target.checked)
});
