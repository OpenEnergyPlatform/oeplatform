﻿<a href="http://oep.iks.cs.ovgu.de/"><img align="right" width="200" height="200" src="https://avatars2.githubusercontent.com/u/37101913?s=400&u=9b593cfdb6048a05ea6e72d333169a65e7c922be&v=4" alt="OpenEnergyPlatform"></a>

# OpenEnergyPlatform - OEPlatform

The OEP code.

## License / Copyright

This repository is licensed under [GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0.en.html)

## Installation

The open energy platform is built atop an PostgreSQL database. Create a new database to avoid clashes.

This project is developed in Python 3.4 and therefore all later uses of pip and python should call the corresponding versions.  

### Setup the python

Once this is done, you can proceed with the installation of the actual platform by cloning the repository. Uninstall django-bootstrap3:

    pip uninstall django-bootstrap3

Install the required python libraries:

    pip install -r requirements.txt

### Setup the databases

The OEP relied on two different databases: One that is managed by django itself. 
This data base contains all informations that are needed to provide the features
of the databases (e.g. user management, revision handling, etc.). The second one
contains data that will be displayed in the data visualisations on the oedb.

#### 1. Django internal database

##### 1.1 Posgresql command line setup

Once logged into your psql session (for example `sudo -u postgres psql`), run the following lines:

    create user oep_django_user with password '<oep_django_password>';
    create database oep_django with owner = oep_django_user;

##### 1.2 Django setup

Create a file oeplatform/securitysettings.py by omitting the '.default' suffix on oeplatform/securitysettings.py.default and enter the connection to your above mentioned postgresql database.

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'oep_django',
    	'USER': 'oep_django_user',
    	'PASSWORD': '<oep_django_password>',
    	'HOST': 'localhost'                      
    	}
    }

By default, the environment variable `OEP_DB_USER` will provide a value for the `USER` field.
The same holds between the environment variable `OEP_DB_PASSWORD` and `PASSWORD` field.

Next step is to migrate the database schema from django to your django database:

    python manage.py migrate


#### 2. OEDB-like Database

This database corresponds to the OEDB (OpenEnergyDataBase) in the live version.
The database connection should point to another *local* postgresql database.
It is used for the data input functionality implemented in `dataedit/`.
If this is the first setup of the OEP, this database should be an empty database as
it will be instantiated by automated scripts later on.

    dbuser = ""
    dbpasswd = ""
    dbport = 5432
    dbhost = ""
    db = ""

##### 2.1 Posgresql command line setup

Once logged into your psql session (for example `sudo -u postgres psql`), run the following lines:

    create user oep_db_user with password '<oep_db_password>';
    create database oep_db with owner = oep_db_user;

Then enter in `oep_db` (`\c oep_db;`) and type the additional commands:

    create extension postgis;
    create extension postgis_topology;
    create extension hstore;

##### 2.2 Django setup

The values of the following variables matched to environment variables' values:

| variable | environment variable  | required |
|---|---|---|
| dbuser | LOCAL_DB_USER  |yes|
| dbpasswd | LOCAL_DB_PASSWORD |yes|
| dbport | LOCAL_DB_PORT |no|
| dbhost | LOCAL_DB_HOST |no|
| dbname | LOCAL_DB_NAME |no|

Make sure to set the required environment variable before performing the next step!

If you kept the default name from the above example in 2.1, then the environment variables
`LOCAL_DB_USER` and `LOCAL_DB_NAME` should have the values `oep_db_user` and `oep_db`, respectively

##### 2.3 Alembic setup

In order to run the OEP, this database needs some management tables.
We use `alembic` to keep track of changes in those tables. To create all tables that are needed
in this oedb-like database:

    python manage.py alembic upgrade head

Only the following schemas are displayed in the dataview app of the OEP. Thus at
least one should be present if you want to use this app:

* demand
* economy
* emission
* environment
* grid
* boundaries
* society
* supply
* scenario
* climate
* model_draft
* openstreetmap
* reference

### Deploy locally
  
You can run your local copy of this platform with:

    python manage.py runserver
    
Per default, you should be able to connect to this copy by visiting [localhost:8000](http://localhost:8000) in your web browser.

## User Management

If the Debug-mode is enabled, the user management is set to a Django-internal manager. Thus, developers are not forced to create accounts in the linked wiki, but can use create a local user 'test' with password 'pass' by running in your project directory: `DJANGO_SETTINGS_MODULE="oeplatform.settings" python` and paste the following code.

    import django
    django.setup()
    from login.models import myuser
    u = myuser.objects.create_user('test','test@mail.com')
    u.set_password('pass')
    u.save()

