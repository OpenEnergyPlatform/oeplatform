#!/usr/bin/env python

# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
#
# SPDX-License-Identifier: MIT

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oeplatform.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
