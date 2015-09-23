from django.conf import settings


class DummySessionForAPIUrls:

    def process_response(self, request, response):
        """
        If this is an API URL, don't create a session for it.
        TODO(jamalex): determine which middleware is creating sessions in the first place, and fix that.
        """
        do_not_create_session = False
        for prefix in ["/download/", "/securesync/api/", "/media/", "/static/", "/api/"]:
            if request.path.startswith(prefix):
                do_not_create_session = True
                break
        if do_not_create_session:
            request.session.modified = False
            request.session.accessed = False
        return response

