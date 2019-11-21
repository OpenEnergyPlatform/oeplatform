<a href="http://oep.iks.cs.ovgu.de/"><img align="right" width="200" height="200" src="https://avatars2.githubusercontent.com/u/37101913?s=400&u=9b593cfdb6048a05ea6e72d333169a65e7c922be&v=4" alt="OpenEnergyPlatform"></a>

# Open Energy Family - Open Energy Platform (OEP)

Repository for the code of the Open Energy Platform (OEP) website [http://openenergy-platform.org/](http://openenergy-platform.org/). This repository does not contain data, for data access please consult [this page](https://github.com/OpenEnergyPlatform/organisation/blob/master/README.md) 

## License / Copyright

This repository is licensed under [GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0.en.html)

## Installation

The installation steps have been proofed on linux and windows for python 3.6 and 3.7. Be aware that some of the required packages present installation's difficulties on windows


### Setup the repository

Clone the repository locally

    git clone https://github.com/OpenEnergyPlatform/oeplatform.git oep-website


Move to the cloned repository

    cd oep-website 


### Setup virtual environment


If you are a windows user, we recommand you use conda because of the dependency on the `shapely` package

1)      conda env create –n oep-website
2)      activate oep-website
3)      conda config –add channels conda-forge
4)      conda install shapely
5)      pip install –r requirements.txt


If you don't want to use conda, [here](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) you can find instructions for setting up virtual environment


After you have activated your virtual environment, install the required python libraries

    pip install -r requirements.txt



### Setup the databases

The OEP website relies on two different databases: 
1. One that is managed by django itself (django internal database)
This database contains all information that is needed for the website (user management, factsheets and api token for connection to the second database). 
2. The second one
will contain the data that the user can access from the website (primary database)

#### 1. Django internal database
##### 0.1 Install postgresql

If postgresql is not installed yet on your computer, you can follow this [guide](https://wam.readthedocs.io/en/latest/getting_started.html#installation-from-scratch)

##### 1.1 Posgresql command line setup

Once logged into your psql session (for linux: `sudo -u postgres psql`, for windows: `psql`), run the following lines:

    create user oep_django_user with password '<oep_django_password>';
    create database oep_django with owner = oep_django_user;

##### 1.2 Django setup

In the repository, copy the file `oeplatform/securitysettings.py.default` and rename it `oeplatform/securitysettings.py`. Then, enter the connection to your above mentioned postgresql database.

Create the environment variables `OEP_DJANGO_USER` and `OEP_DJANGO_PW` with values `oep_django_user` and `<oep_django_password>`, respectively.

For default settings, you can type the following commands

- On windows

     before you can set environment variables in your terminal you should first type `cmd/v`

      set OEP_DJANGO_USER=oep_django_user
      set OEP_DJANGO_PW=<oep_django_password>
    

- On linux

      export OEP_DJANGO_USER=oep_django_user
      export OEP_DJANGO_PW=<oep_django_password>

Finish the django database setup with this command

    python manage.py migrate


#### 2. Primary Database


This database is used for the data input functionality implemented in `dataedit/`.

If this is your first local setup of the OEP website, this database should be an empty database as
it will be instantiated by automated scripts later on.

##### 2.1 Posgresql command line setup

Once logged into your psql session (for linux: `sudo -u postgres psql`, for windows: `psql`), run the following lines:

    create user oep_db_user with password '<oep_db_password>';
    create database oep_db with owner = oep_db_user;

Then enter in `oep_db` (`\c oep_db;`) and type the additional commands:

    create extension postgis;
    create extension postgis_topology;
    create extension hstore;

##### 2.2 Database connection setup

| environment variable  | required |
|---|---|
| LOCAL_DB_USER  |yes|
| LOCAL_DB_PASSWORD |yes|
| LOCAL_DB_PORT |no|
| LOCAL_DB_HOST |no|
| LOCAL_DB_NAME |no|

Make sure to set the required environment variables before going to the next section!

For default settings, you can type the following commands

- On windows

      set LOCAL_DB_USER=oep_db_user
      set LOCAL_DB_PASSWORD=<oep_db_password>
      set LOCAL_DB_NAME=oep_db
    

- On linux

      export LOCAL_DB_USER=oep_db_user
      export LOCAL_DB_PASSWORD=<oep_db_password>
      export LOCAL_DB_NAME=oep_db


Note, if you kept the default name from the above example in 2.1, then the environment variables
`LOCAL_DB_USER` and `LOCAL_DB_NAME` should have the values `oep_db_user` and `oep_db`, respectively

##### 2.3 Alembic setup

In order to run the OEP website, the primary database needs some extra management tables.
We use `alembic` to keep track of changes in those tables. To create all tables that are needed, simply type

    python manage.py alembic upgrade head

### Deploy locally
  
You can run your local copy of the OEP website with

    python manage.py runserver
    
By default, you should be able to connect to this copy by visiting [localhost:8000](http://localhost:8000) in your web browser.


### User Management

To create a dummy user for functionality testing purposes

- On windows

      set DJANGO_SETTINGS_MODULE=oeplatform.settings

- On linux

      export DJANGO_SETTINGS_MODULE=oeplatform.settings

Then execute this python code (either directly in a terminal or from a file)

      import django
      django.setup()
      from login.models import myuser
      u = myuser.objects.create_devuser('test','test@mail.com')
      u.set_password('pass')
      u.save()

## Code contribution

Please read carefully the `CONTRIBUTE.md` [file](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/CONTRIBUTE.md) before you start contributing!
