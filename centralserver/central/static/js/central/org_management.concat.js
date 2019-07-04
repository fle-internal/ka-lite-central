/***********************************************************************************************************************
Some functionality that we needed from the distributed server. Copied here & modified to run without complicated
dependencies.

Removed references to statusModel in particular... doesn't seem to be used on the central server.
***********************************************************************************************************************/
function getQueryParams(url) {
    /*
    Get the query parameters from a url string and returns them as an object.
    :param url: a string, e.g. "http://example.com/?foo=bar&baz=boo"
    :returns: an object e.g. {foo: "bar", baz: "boo"}
    */

    query_re = /\?(([^=]+=[^=&]*&?)+)$/;
    // Expected output: query_re.exec("http://example.com/?foo=bar&baz=boo&blah=")[1] === "foo=bar&baz=boo&blah="

    match = query_re.exec(url)
    queries = match ? match[1].split("&") : null;
    if (queries) {
        queries = _.reduce(queries, function(query_obj, query){
            key = query.split("=")[0];
            value = query.split("=")[1];
            query_obj[key] = value;
            return query_obj;
        }, {});
    }
    return queries;
}

function doRequest(url, data, opts) {
    // If locale is not already set, set it to the current language.
    var query;

    if ((query = getQueryParams(url)) === null) {
      query = {};
    }

    /*
    Is the "lang" param used on the central server? Doesn't appear to be. But leaving this here for now
    in case we miss it. MCGallaspy.
    if (query.lang === undefined && data !== null && data !== undefined) {
        if (!data.hasOwnProperty('lang')) {
            url = get_params.setGetParam(url, "lang", window.sessionModel.get("CURRENT_LANGUAGE"));
        }
    }
    */

    var request_options = {
        url: url,
        type: data ? "POST" : "GET",
        data: data ? JSON.stringify(data) : "",
        contentType: "application/json",
        dataType: "json"
    };
    var error_prefix = "";

    for (var opt_key in opts) {
        switch (opt_key) {
            case "error_prefix":  // Set the error prefix on a failure.
                error_prefix = opts[opt_key];
                break;
            default:  // Tweak the default options
                request_options[opt_key] = opts[opt_key];
                break;
        }
    }
    // TODO-BLOCKER (rtibbles): Make setting of the success and fail callbacks more flexible.
    return $.ajax(request_options)
        .success(function(resp) {
            handleSuccessAPI(resp);
        })
        .fail(function(resp) {
            handleFailedAPI(resp, error_prefix);
        });
}

function handleSuccessAPI(obj) {

    var messages = null;
    var msg_types = ["success", "info", "warning", "error"];  // in case we need to dig for messages


    if (!obj) {
        return;

    } else if (obj.hasOwnProperty("responseText")) {
        // Got a HTTP response object; parse it.
        try {
            if (obj.responseText) {  // No point in trying to parse empty response (which is common)
                messages = $.parseJSON(obj.responseText);
            }
        } catch (e) {
            // Many reasons this could fail, some valid; others not.
            console.log(e);
        }
    } else if (obj.hasOwnProperty("messages")) {
        // Got messages embedded in the object
        messages = {};
        for (var idx in obj.messages) {
            messages = obj.messages[idx];
        }
    } else {
        // Got messages at the top level of the object; grab them.
        messages = {};
        for (var idy in msg_types) {
            var msg_type = msg_types[idy];
            if (msg_type in obj) {
                messages[msg_type] = obj[msg_type];
                console.log(messages[msg_type]);
            }
        }
    }

    if (messages) {
        show_api_messages(messages);
    }
}

function handleFailedAPI(resp, error_prefix) {
    // Two ways for this function to be called:
    // 1. With an API response (resp) containing a JSON error.
    // 2. With an explicit error_prefix

    // TODO(jamalex): simplify this crud; "error_prefix" doesn't even seem to get used at all?

    // Parse the messages.
    var messages = {};
    switch (resp.status) {
        case 0:
            messages = {error: gettext("Could not connect to the server.") + " " + gettext("Please try again later.")};
            break;

        case 401:

        case 403:
            messages = {error: gettext("You are not authorized to complete the request.  Please login as an authorized user, then retry the request.")};
            break;

        default:

            try {
                messages = $.parseJSON(resp.responseText || "{}").messages || $.parseJSON(resp.responseText || "{}");
            } catch (e) {
                // Replacing resp.responseText with "There was an unexpected error!" is just a workaround... this should be fixed.
                // See https://github.com/learningequality/ka-lite/issues/4203
                var error_msg = sprintf("%s<br/>%s<br/>%s", resp.status, "There was an unexpected error!", resp);
                messages = {error: sprintf(gettext("Unexpected error; contact the FLE with the following information: %(error_msg)s"), {error_msg: error_msg})};
                console.log("Response text: " + resp.responseText);
                console.log(e);
            }
            break;
    }

    clear_messages();  // Clear all messages before showing the new (error) message.
    show_api_messages(messages);
}

function show_api_messages(messages) {
    // When receiving an error response object,
    //   show errors reported in that object
    if (!messages) {
        return;
    }
    switch (typeof messages) {
        case "object":
            for (var msg_type in messages) {
                show_message(msg_type, messages[msg_type]);
            }
            break;
        case "string":
            // Should throw an exception, but try to handle gracefully
            show_message("info", messages);
            break;
        default:
            // Programming error; this should not happen
            // NOTE: DO NOT WRAP THIS STRING.
            throw "do not call show_api_messages object of type " + (typeof messages);
    }
}

function show_message(msg_class, msg_text, msg_id) {
    // This function is generic--can be called with server-side messages,
    //    or to display purely client-side messages.
    // msg_class includes error, warning, and success
    if (msg_id === undefined) {
        // Only do this if msg_text and its hashCode are both defined
        if ((typeof msg_text !== "undefined" ? msg_text.hashCode : void 0)) {
            msg_id = msg_text.hashCode();
        }
    }

    // Avoid duplicating the same message by removing any existing message with the same id
    if (msg_id) {
        $("#" + msg_id).remove();
    }

    if (!msg_text) {
        return $("#message_container");
    }

    var x_button = '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>';

    if (msg_class === "error") {
        msg_class = "danger";
    }
    var msg_html = "<div class='alert alert-" + msg_class + "'";

    if (msg_id) {
        msg_html += " id='" + msg_id + "'";
    }
    msg_html += ">" + x_button + msg_text + "</div>";
    $("#message_container").append(msg_html);
    return $("#message_container");
}

function clear_messages(msg_type) {
    if (!msg_type) {
        // Clear all messages
        $("#message_container .alert").remove();
    } else {
        $("#message_container .alert-" + msg_type).remove();
    }
    return $("#message_container");
}
$(function() {
    // makes correct link submit form for removing admin & revoking invites
    $('.remove-admin-submit, .remove-invite-submit').click(function() {
        $(this).parent('form').submit();
        return false;
    });

    /*
        setting up glossary
    */
    $('.glossary-link').wrap(sprintf('<a href="%s"></a>', GLOSSARY_URL));

    // Used <div> instead of <a> to avoid a dirty js hack to avoid the reload to top page.
    $('.button-popover-zone').each(function() { $(this).popover(); }); //Each popover needs an individual callback
    $('.button-popover-orgadmin').each(function() { $(this).popover(); });

    $('#button-popover-org').popover()
    $('#button-popover-headless').popover()

    $('body').on('click', function (e) {
        $('.button-popover').each(function () {
            //the 'is' for buttons that trigger popups
            //the 'has' for icons within a button that triggers a popup
            if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
                $(this).popover('hide');
            }
        });
    });

    /*
        Deletions
    */

    $(".zone-delete-link").click(function(event) {
        if (confirm(gettext("Are you sure you want to delete this sharing network?"))) {
            var delete_zone_url = event.target.getAttribute("value");
            doRequest(delete_zone_url)
                .success(function() {
                    window.location.reload();
                });
        }
    });

    $(".org-delete-link").click(function(event) {
        if (confirm(gettext("Are you sure you want to delete this organization?"))) {
            var delete_org_url = event.target.getAttribute("value");
            doRequest(delete_org_url)
                .success(function() {
                    window.location.reload();
                });
        }
    });
});
