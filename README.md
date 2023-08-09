[![Documentation Status](https://readthedocs.org/projects/oeplatform/badge/?version=latest)](https://oeplatform.readthedocs.io/en/latest/?badge=latest)

<a href="https://openenergy-platform.org/"><img align="right" width="200" height="200" src="https://avatars2.githubusercontent.com/u/37101913?s=400&u=9b593cfdb6048a05ea6e72d333169a65e7c922be&v=4" alt="OpenEnergyPlatform"></a>

# Open Energy Family - Open Energy Platform (OEP)

Repository for the code of the Open Energy Platform (OEP) website [https://openenergy-platform.org/](https://openenergy-platform.org/). This repository does not contain data, for data access please consult [this page](https://github.com/OpenEnergyPlatform/organisation/blob/master/README.md)

## License / Copyright

This repository is licensed under [GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0.en.html)

# Installation


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

Please read carefully the `CONTRIBUTING.md` [file](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/CONTRIBUTING.md) before you start contributing!
