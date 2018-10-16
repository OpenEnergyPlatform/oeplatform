from django.conf import settings
from django.http import HttpResponseRedirect

DETACH_PATH = '/user/detach'
class DetachMiddleware(object):
    def process_request(self, request):
        if not request.user.is_anonymous \
                and not request.user.is_native \
                and not request.path == DETACH_PATH \
                and not request.path == '/login/' \
                and not request.path.startswith('/api'):
            return HttpResponseRedirect(DETACH_PATH)