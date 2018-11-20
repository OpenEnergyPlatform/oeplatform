from django.conf import settings
from django.http import HttpResponseRedirect

DETACH_PATH = '/user/detach'
ACTIVATE_PATH = '/user/activate'

class DetachMiddleware(object):
    def process_request(self, request):
        if not request.path == '/login/' \
                and not request.path.startswith('/api')  \
                and not request.user.is_anonymous:

            if not request.user.is_native:
                if not (request.path == DETACH_PATH
                        or request.path.startswith('/logout')):
                    return HttpResponseRedirect(DETACH_PATH)
            elif not request.user.is_mail_verified \
                    and not (ACTIVATE_PATH in request.path
                             or request.path.startswith('/logout')):
                return HttpResponseRedirect(ACTIVATE_PATH)