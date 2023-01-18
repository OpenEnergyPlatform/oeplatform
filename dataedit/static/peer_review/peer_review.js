var peerReview = function (config) {
    var state = {
        "topic": null,
        "table": config.table,
        "reviewList": [],
        "metaMetadata": {
            "reviewVersion": "OEP-0.0.1",
            "metadataLicense": {
                "name": "CC0-1.0",
                "title": "Creative Commons Zero v1.0 Universal",
                "path": "https://creativecommons.org/publicdomain/zero/1.0/"
            }
        }
    }

    /*
    TODO: consolidate functions (same as in wizard and other places)
    */

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            var cookies = document.cookie.split(";");
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function getCsrfToken() {
        var token1 = getCookie("csrftoken");
        return token1;
    }

    function sendJson(method, url, data, success, error) {
        var token = getCsrfToken();
        return $.ajax({
            url: url,
            headers: { "X-CSRFToken": token },
            data_type: "json",
            cache: false,
            contentType: "application/json; charset=utf-8",
            processData: false,
            data: data,
            type: method,
            success: success,
            error: error
        });
    }

    function getErrorMsg(x) {
        try {
            x = 'Upload failed: ' + JSON.parse(x.responseJSON).reason;
        } catch (e) {
            x = x.statusText;
        }
        return x;
    }

    function bindButtons() {
        // submit
        $('#peer_review-submit').bind('click', function submitPeerReview() {
            $('#peer_review-submitting').removeClass('d-none');
            var json = config.editor.getValue();
            json = fixData(json);
            json = JSON.stringify(json);
            sendJson("POST", config.url_api_meta, json).then(function () {
                window.location = config.url_view_table;
            }).catch(function (err) {
                // TODO evaluate error, show user message
                $('#peer_review-submitting').addClass('d-none');
                alert(getErrorMsg(err))
            });
        });

        // Cancel
        $('#peer_review-cancel').bind('click', function cancel() {
            window.location = config.cancle_url;
        })
    }

    (function init() {

        $('#peer_review-loading').removeClass('d-none');

        config.form = $('#peer_review-form');

        bindButtons();




    })();

    return config;

}
