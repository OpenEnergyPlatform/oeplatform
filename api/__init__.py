try:
    from oeplatform.settings import DEFAULT_SCHEMA  # noqa
except Exception:
    import logging

    logging.error("No securitysettings found")
