from django.conf import settings


class DummySessionForAPIUrls:

    def process_response(self, request, response):
        """
        If this is an API URL, don't create a session for it.
        TODO(jamalex): avoid importing unnecessary middleware from facility, i18n, etc, which touch
        the session object and create useless sessions -- to make this silly middleware obsolete.
        """
        do_not_create_session = False
        for prefix in ["/download/", "/securesync/api/"]:
            if request.path.startswith(prefix):
                do_not_create_session = True
                break
        if do_not_create_session:
            request.session.modified = False
            request.session.accessed = False
        return response

