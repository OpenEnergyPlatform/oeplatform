# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
#
# SPDX-License-Identifier: MIT

class MetadataException(Exception):
    def __init__(self, metadata, error):
        self.metadata = metadata
        self.error = error
