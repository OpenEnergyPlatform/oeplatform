import logging
import os

from django.apps import AppConfig

from oeplatform.settings import DOCUMENTATION_LINKS, OPEN_ENERGY_ONTOLOGY_FOLDER


class OntologyConfig(AppConfig):
    name = "ontology"

    def ready(self):
        """
        Check if the necessary oeo release files are available. This check is
        strict to the expected directory structure that is defined in
        the settings / secSettings.
        It is not checked weather the files actually exists but it is checked
        if the oeo folder is available. This folder should only be available
        if it was downloaded before.

        Returns a understandable error massage that also links to the related
        documentation.
        """
        # Specify the file to check
        file_to_check = OPEN_ENERGY_ONTOLOGY_FOLDER

        # Configure the logging module
        logging.basicConfig(level=logging.WARNING)
        logger = logging.getLogger(__name__)

        # Check if the file exists during app startup
        # file_path = os.path.(file_to_check)
        if not os.path.exists(file_to_check):
            logger.error(
                f"The oeo release files in '{file_to_check}' are missing! "
                "The app can`t start.!"
            )
            raise ImportError(
                f"The oeo release files in '{file_to_check}' are missing! "
                "The app can`t start. Please refer to the documentation: "
                f"{DOCUMENTATION_LINKS.get('oeo_setup')}"
            )
