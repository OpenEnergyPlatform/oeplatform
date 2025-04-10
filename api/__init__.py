# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@gmail.com>
# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@googlemail.com>
# SPDX-FileCopyrightText: 2025 jh-RLI <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

try:
    from oeplatform.securitysettings import DEFAULT_SCHEMA  # noqa
except Exception:
    import logging

    logging.error("No securitysettings found")
