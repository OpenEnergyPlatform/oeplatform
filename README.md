<a href="http://oep.iks.cs.ovgu.de/"><img align="right" width="200" height="200" src="https://avatars2.githubusercontent.com/u/37101913?s=400&u=9b593cfdb6048a05ea6e72d333169a65e7c922be&v=4" alt="OpenEnergyPlatform"></a>

# OpenEnergyPlatform - OEPlatform

The OEP code.

## License / Copyright

This repository is licensed under [GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0.en.html)

## Installation

The open energy platform is built atop an PostgreSQL database. Create a new database to avoid clashes.

This project is developed in Python 3.4 and therefore all later uses of pip and python should call the corresponding versions.  

Once this is done, you can proceed with the installation of the actual platform by cloning the repository. Install the required python libraries:

    pip install -r requirements.txt

Create a file oeplatform/securitysettings.py by omitting the '.default' prefix on oeplatform/securitysettings.py.default and enter the connection to your above mentioned postgresql database.

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'django',
    	'USER': 'databaseuser',
    	'PASSWORD': 'databasepassword',
    	'HOST': 'localhost'                      
    	}
    }

The second database connection should point to another postgresql database. It is used for the data input functionality implemented in dataedit/.

    dbuser = ""
    dbpasswd = ""
    dbport = 5432
    dbhost = ""
    db = ""

You have to include a third database, which is used for testing. This database shouldn't include productive data.

Make sure that both databases has the following extensions installed:
      
* hstore               
* postgis         
* postgis_topology

Next step is to migrate the database schema from django to your django database:

    python manage.py migrate
  
Finally, you can run your local copy of this platform:

    python manage.py runserver
    
Per default, you should be able to connect to this copy by visiting [localhost:8000](http://localhost:8000) in your web browser.

## User Management

If the Debug-mode is enabled, the user management is set to a Django-internal manager. Thus, developers are not forced to create accounts in the linked wiki, but can use create a local user 'test' with password 'pass' by running: 

    from login.models import myuser
    u = myuser.objects.create_user('test','test@mail.com')
    u.set_password('pass')
    u.save()

