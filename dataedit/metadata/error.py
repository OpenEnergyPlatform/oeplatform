# SPDX-FileCopyrightText: 2025 Martin Glauer <martinglauer89@gmail.com>
#
# SPDX-License-Identifier: MIT

class MetadataException(Exception):
    def __init__(self, metadata, error):
        self.metadata = metadata
        self.error = error
