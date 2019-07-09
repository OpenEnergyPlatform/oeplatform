from django.http import HttpResponse


class ModHttpResponse(HttpResponse):
    def __init__(self, dictonary):

        if dictonary is None:
            HttpResponse.__init__(self, status=500)
            return

        if dictonary["success"]:
            HttpResponse.__init__(self, status=200)
            return

        # TODO: Find smarter way to just define a parameter, if an expression is true.
        if dictonary["error"] is not None:
            HttpResponse.__init__(
                self, status=dictonary["http_status"], reason=dictonary["error"]
            )
            return
        else:
            HttpResponse.__init__(self, status=dictonary["http_status"])
            return
