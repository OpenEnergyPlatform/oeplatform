try:
    from oeplatform.securitysettings import DEFAULT_SCHEMA
except:
    import logging

    logging.error("No securitysettings found")
