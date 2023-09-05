# Developement & Collaoration

!!! warning
    This page will be updated soon.

## Getting started with the developement 

See our [developer guidelines](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/CONTRIBUTING.md) and get in touch with our [developer team](https://openenergyplatform.github.io/organisation/family_community/contact/).

### Deploy locally

You can run your own local copy of the OEP website with

    python manage.py runserver

By default, you should be able to connect to this copy by visiting [localhost:8000](http://localhost:8000) in your web browser.
This way you can insert your changes without worrying about breaking anything in the production system.

## User Management

To create a dummy user for functionality testing purposes

Then execute this python code (either directly in a terminal or from a file)
    
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oeplatform.settings")
    django.setup()
    django.setup()
    from login.models import myuser
    u = myuser.objects.create_devuser('test','test@mail.com')
    u.set_password('pass')
    u.save()