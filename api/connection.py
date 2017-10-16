import sqlalchemy as sqla
import oeplatform.securitysettings as sec

__ENGINE = sqla.create_engine(
    'postgresql://{0}:{1}@{2}:{3}/{4}'.format(
        sec.dbuser,
        sec.dbpasswd,
        sec.dbhost,
        sec.dbport,
        sec.dbname), pool_size=0)

def _get_engine():
    return __ENGINE

