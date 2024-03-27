# Development setup

See our [developer guidelines](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/CONTRIBUTING.md) and get in touch with our [developer team](https://openenergyplatform.github.io/organisation/family_community/contact/).

## Choose your development environment and tools

As a software developer, you learn your own way of working and refine it as your experience grows. The choice of developer environment & tools is therefore largely a personal preference. Here we want to suggest how new developers can get started and how we can implement successful, efficient development. 

In addition, there are some tools that are absolutely necessary to ensure the quality of the software while new code from various sources is collaboratively fed into a code repository on github.

### The operating system

In our installation guide we offer the installation for all common OS (Linux/Apple, Windows). Since the server on which the developed software (especially web applications) is operated is usually a Linux-based system, it is also highly advisable to design the local development environment as similarly as possible.

Especially for developers using a Windows computer, there are relevant considerations here to avoid constant additional work that is necessary to install certain packages in order to remain compatible with the latest developments.

Those who want to participate in software development in the long term should therefore consider whether it is worth using either a container solution such as [Docker](https://www.docker.com/products/docker-desktop/) in which the software and databases are installed. New code can then be written or tested directly in the container via an IDE. On the other hand, [WSL](https://learn.microsoft.com/de-de/windows/wsl/install) has also been available for some time, which can be used to run a Linux system on a Windows computer. As Microsoft itself developed the solution, it is particularly well integrated.

### Development tools

We mainly use VSCode or PyCharm as an integrated development environment (IDE). These IDEs are particularly easy to install, can be flexibly extended with plugins and enable all relevant tools for development to be operated in one window, which in our view increases productivity.

## Run all tests

We aim to develop the oeplatform by using the test driven development approach. Fundamentally this requires a testing framework that is provided by [django](https://docs.djangoproject.com/en/3.2/topics/testing/). If you want to check if your changes to the codebase affect the existing functionality run all available tests:

    python manage.py test

Most of our current tests are available in the `api` app of the django project. Look for the `tests` directory in any of our apps.

## Deploy locally

You can run your own local copy of the OEP website server with

    python manage.py runserver

By default, you should be able to connect to this copy by visiting [localhost:8000](http://localhost:8000) in your web browser.
This way you can insert your changes without worrying about breaking anything in the production system.

## User Management - Setup a test user

To create a dummy user for functionality testing purposes

Then execute this python code (either directly in a terminal or from a file)

    import os    
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oeplatform.settings")
    django.setup()
    from login.models import myuser
    u = myuser.objects.create_devuser('test','test@mail.com')
    u.set_password('pass')
    u.save()

## Create test tables

You have multiple options to create tables and upload data. We will not explain the approach using a SQL dump that is imported into the postgresql database. The easiest approach that will get you started quickly is based on the OEP-Website UI. The related functionality is part of the `dataedit` app in the django project.

Before we can get started we have to register the topics where data can be grouped to. Initially all data is uploaded to the topic `model_draft`. Once it is published it is moved to another topic e.g. `demand` or `scenario`. You can use the management command to register our predefined topics:

    python manage.py create_topics

### Using the HTTP-API

You can either use the http api that is available once you started your local development server using the `runserver` command. To understand how to use the api you can have a look at our academy courses but keep in mind that you have to modify the URL of the api endpoints to you locally running oep instance. You can to this by changing the beginning of the url from something like `https://www.oeplatform.org/` to `http://127.0.0.1/`. [Have a look at this course to get started with the http api.](https://openenergyplatform.github.io/academy/tutorials/01_api/02_api_upload/)

### Using the OEP-Website UI

The OEP-Website includes a features that is called upload wizard internally. This features usually is used by the user to add datasets to the `model_draft` topic and can be accessed via the database page. Initially the database is empty and the topic cards are not visible. You have to navigate to the page manually. Once you have started your local instance of the OEP you can navigate to this URL:

    http://127.0.0.1/dataedit/wizard/

There you can create a table, upload data from CSV file, create metadata and then navigate to the table page. To get started it is okay to just create a table with minimal requirements by just adding a table name that is all lowercase and does not include whitespaces, - or any special characters.

## Publish aka move datasets

Once you created your test data you probably want to move your data to any of the other topics. This functionality is also available via the Website UI and by using another endpoint of the HTTP-API.

### Via the HTTP-API

There is no tutorial available for this feature. You can send a post request to the following URL. You need to add your api token to the post request header. You can have a look on the table create tutorial linked above to understand how you can do that. In python you can use the package `requests` to perform http requests.

    http://127.0.0.1/v0/schema/<str:schema>/tables/<str:table>/move/<str:to_schema>/

The URL must include the name of the topic and table you want to move and the name of the topic you want to move table to. In the future this endpoint will change because it is part of the publishing process. Moving a table will then only be possible once the metadata for that table includes an open data license.

### Via the OEP-Website UI

You can navigate to the profile page using your local instance of the OEP website.

    http://127.0.0.1/user/profile/

There you find a tab called tables. If you include an open data license in the metadata of your test table you previously create in the `model_draft` topic, a publish button becomes visible. Once you click it you can select a topic to move the table to.

You can edit the metadata for a table by visiting the detail page of a table then click the tab meta information and click the button edit. The license information should be added to the licenses field of the metadata.
