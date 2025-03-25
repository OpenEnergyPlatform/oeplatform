# SPDX-FileCopyrightText: 2017 Martin Glauer <MGlauer>
# SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
# SPDX-License-Identifier: MIT

class MetadataException(Exception):
    def __init__(self, metadata, error):
        self.metadata = metadata
        self.error = error
