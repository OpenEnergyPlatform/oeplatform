# SPDX-FileCopyrightText: 2017 Martin Glauer <MGlauer>
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT

class APIError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status


class APIKeyError(APIError):
    def __init__(self, dictionary, key):
        self.message = "Key '%s' not found in %s" % (key, dictionary)
        self.status = 401
