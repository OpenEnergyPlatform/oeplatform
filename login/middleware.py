from django.conf import settings
from django.http import HttpResponseRedirect

DETACH_PATH = '/user/detach'
ACTIVATE_PATH = '/user/activate'

class DetachMiddleware(object):
    def process_request(self, request):
        if not request.path == '/login/' \
                and not request.path.startswith('/api'):

            if not request.user.is_anonymous \
                    and not request.user.is_native \
                    and not request.path == DETACH_PATH:
                return HttpResponseRedirect(DETACH_PATH)

            if not request.user.is_anonymous \
                    and not request.user.is_mail_verified \
                    and not request.path.startswith(ACTIVATE_PATH):
                return HttpResponseRedirect(ACTIVATE_PATH)