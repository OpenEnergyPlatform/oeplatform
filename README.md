# oeplatform
The open energy platform of open_eGo

## Installation

The open energy platform is built atop an PostgreSQL database. Create a new database to avoid clashes.

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

Next step is to migrate the database shema from django to your django database:

    python manage.py makemigrations
    python manage.py migrate
  
Finally, you can run your local copy of this platform:

    python manage.py runserver
