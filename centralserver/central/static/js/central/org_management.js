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
            console.log('b');
            //the 'is' for buttons that trigger popups
            //the 'has' for icons within a button that triggers a popup
            if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
                $(this).popover('hide');
            }
        });
    });

    /*
        end setting up glossary
    */
});
