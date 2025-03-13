# SPDX-FileCopyrightText: 2017 Johann Wagner <johannwagner>
# SPDX-FileCopyrightText: 2019 Martin Glauer <MGlauer>
# PDX-FileCopyrightText: 2024 Eike Broda <ebroda>
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT

from django.http import HttpResponse


class ModHttpResponse(HttpResponse):
    def __init__(self, dictionary):
        if dictionary is None:
            HttpResponse.__init__(self, status=500)
            return

        if dictionary["success"]:
            HttpResponse.__init__(self, status=200)
            return

        # TODO: Find smarter way to just define a parameter, if an expression is true.
        if dictionary["error"] is not None:
            HttpResponse.__init__(
                self, status=dictionary["http_status"], reason=dictionary["error"]
            )
            return
        else:
            HttpResponse.__init__(self, status=dictionary["http_status"])
            return
