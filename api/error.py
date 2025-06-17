# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: AGPL-3.0-or-later

class APIError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status


class APIKeyError(APIError):
    def __init__(self, dictionary, key):
        self.message = "Key '%s' not found in %s" % (key, dictionary)
        self.status = 401
