import sqlalchemy as sqla

try:
    import oeplatform.securitysettings as sec
except:
    import logging
    logging.error("No securitysettings found. Triggerd in api/connection.py")

def get_connection_string():
    return "postgresql://{0}:{1}@{2}:{3}/{4}".format(
        sec.dbuser, sec.dbpasswd, sec.dbhost, sec.dbport, sec.dbname
    )


__ENGINE = sqla.create_engine(
    get_connection_string(), pool_size=0, pool_recycle=600, max_overflow=200
)


def _get_engine():
    return __ENGINE
