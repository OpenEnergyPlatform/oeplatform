# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Eike Broda <git@ebroda.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
# SPDX-FileCopyrightText: 2025 MGlauer <martinglauer89@gmail.com>
# SPDX-FileCopyrightText: 2025 c.winger <c.winger@oeko.de>
#
# SPDX-License-Identifier: MIT

import logging
import os

from django.apps import AppConfig

from oeplatform.settings import DOCUMENTATION_LINKS, OPEN_ENERGY_ONTOLOGY_FOLDER, OEO_EXT_OWL_PATH


class OntologyConfig(AppConfig):
    name = "ontology"

    # Configure the logging module
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)

    def ready(self):
        """
        Check if the necessary oeo release files are available. This check is
        strict to the expected directory structure that is defined in
        the settings / secSettings.
        It is not checked whether the files actually exists, but it is checked
        if the oeo folder is available. This folder should only be available
        if it was downloaded before.

        Returns an understandable error message that also links to the related
        documentation.
        """
        # Specify the file to check
        self.check_file(OPEN_ENERGY_ONTOLOGY_FOLDER, 'oeo release', 'oeo_setup')
        self.check_file(OEO_EXT_OWL_PATH, 'oeo extended', 'oeo_ext_setup')

    def check_file(self, file_to_check, file_label, documentation_key):
        # Check if the file exists during app startup
        if not os.path.exists(file_to_check):
            msg = f"The {file_label} files in '{file_to_check}' are missing! " \
            "The app can`t start. Please refer to the documentation: " \
            f"{DOCUMENTATION_LINKS.get(documentation_key)}"

            self.logger.error(msg)
            raise ImportError(msg)
