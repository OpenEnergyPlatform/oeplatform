# SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer>
# SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
#
# SPDX-License-Identifier: MIT

try:
    from oeplatform.securitysettings import DEFAULT_SCHEMA  # noqa
except Exception:
    import logging

    logging.error("No securitysettings found")
