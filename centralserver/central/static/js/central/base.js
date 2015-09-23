function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

$(function() {
    $(".header__horizontal-menu__right").addClass("js").before('<div id="menu">&#9776;</div>');
    $("#menu").click(function(){
      $(".header__horizontal-menu__right").toggle();
    });
    $(window).resize(function(){
      if(window.innerWidth > 768) {
        $(".header__horizontal-menu__right").removeAttr("style");
      }
    });

    // Code below overwrites khan-lite.js setup to ensure that the correct csrftoken is passed for the central server.

    var csrftoken = getCookie("csrftoken_central") || "";

    $.ajaxSetup({
        cache: false,
        crossDomain: false,
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $(".help-tooltip").tooltip({
        placement : 'right'
    });
});