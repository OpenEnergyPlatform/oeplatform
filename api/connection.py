import sqlalchemy as sqla
import oeplatform.securitysettings as sec


def get_connection_string():
    return "postgresql://{0}:{1}@{2}:{3}/{4}".format(
        sec.dbuser, sec.dbpasswd, sec.dbhost, sec.dbport, sec.dbname
    )


__ENGINE = sqla.create_engine(
    get_connection_string(), pool_size=0, pool_recycle=600, max_overflow=200
)


def _get_engine():
    return __ENGINE
