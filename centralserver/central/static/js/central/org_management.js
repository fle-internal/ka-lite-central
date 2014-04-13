$(function() {
    // makes correct link submit form for removing admin & revoking invites
    $('.remove-admin-submit, .remove-invite-submit').click(function(ev) {
        $(ev.srcElement).parents('form').submit();
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
