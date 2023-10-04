from django.http import HttpResponseRedirect

DETACH_PATH = "/user/detach"
ACTIVATE_PATH = "/user/activate"


class DetachMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            not request.path == "/login/"
            and not request.path.startswith("/api")
            and not request.user.is_anonymous
        ):
            if not request.user.is_native:
                if not (
                    request.path == DETACH_PATH or request.path.startswith("/logout")
                ):
                    return HttpResponseRedirect(DETACH_PATH)
            elif not request.user.is_mail_verified and not (
                request.path.startswith(ACTIVATE_PATH)
                or request.path.startswith("/logout")
            ):
                return HttpResponseRedirect(ACTIVATE_PATH)
        return self.get_response(request)
