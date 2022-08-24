try:
    from oeplatform.securitysettings import DEFAULT_SCHEMA  # noqa
except:
    import logging

    logging.error("No securitysettings found")
