# Development setup

!!! Note "Recent updates"

    As we shift the development support towards a docker based setup which sets up the oeplatform infrastructure and deploys it locally most of the commands below are are already included in the automated docker compose setup. For example there is dummy data and a test user pre "installed" and ready to use. Also note that if you use the docker based setup you must run the commands below inside the oeplatform web container to gain any effect.

    Available information which effect your host environment like your IDE and your operating system stay the same.

See our
[developer guidelines](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/CONTRIBUTING.md)
and get in touch with our
[developer team](https://openenergyplatform.github.io/organisation/family_community/contact/).
Have a look at the official
[git-Book](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup)
instructions on how to setup your git on a new system to be able to contribute
to our GitHub repository.

## Choose your development environment and tools

As a software developer, you learn your own way of working and refine it as your
experience grows. The choice of developer environment & tools is therefore
largely a personal preference. Here we want to suggest how new developers can
get started and how we can implement successful, efficient development.

In addition, there are some tools that are absolutely necessary to ensure the
quality of the software while new code from various sources is collaboratively
fed into a code repository on github.

### The operating system

In our installation guide we offer the installation for all common OS
(Linux/Apple, Windows). Since the server on which the developed software
(especially web applications) is operated is usually a Linux-based system, it is
also highly advisable to design the local development environment as similarly
as possible.

Especially for developers using a Windows computer, there are relevant
considerations here to avoid constant additional work that is necessary to
install certain packages in order to remain compatible with the latest
developments.

Those who want to participate in software development in the long term should
therefore consider whether it is worth using either a container solution such as
[Docker](https://www.docker.com/products/docker-desktop/) in which the software
and databases are installed. New code can then be written or tested directly in
the container via an IDE. On the other hand,
[WSL](https://learn.microsoft.com/de-de/windows/wsl/install) has also been
available for some time, which can be used to run a Linux system on a Windows
computer. As Microsoft itself developed the solution, it is particularly well
integrated.

### Development tools

We mainly use VSCode or PyCharm as an integrated development environment (IDE).
These IDEs are particularly easy to install, can be flexibly extended with
plugins and enable all relevant tools for development to be operated in one
window, which in our view increases productivity.

#### pre-commit-hooks

We encourage you to install our pre-commit hooks. They will probably get in the
way sometimes when you try to "just commit" your code, but they help us to
ensure the quality of the code, especially the formatting of the code.

    pip install pre-commit

And install our hooks as defined in the '.pre-commit-config.yaml' file

    pre-commit install

From now on, you can only transfer if the hooks are successful.

### Useful VSCode plugins

You can search the name in the VSCode Extensions tab:

- Black Formatter
- isort
- Flake8
- Pylance
- Python
- Python Debugger
- Code Spell Checker
- Database Client
- ESLint
- markdownlint
- GitLens

## Run all tests

We aim to develop the oeplatform by using the test driven development approach.
Fundamentally this requires a testing framework that is provided by
[django](https://docs.djangoproject.com/en/3.2/topics/testing/). If you want to
check if your changes to the codebase affect the existing functionality run all
available tests:

    python manage.py test

Most of our current tests are available in the `api` app of the django project.
Look for the `tests` directory in any of our apps.

## Deploy locally

You can run your own local copy of the OEP website server with

    python manage.py runserver

By default, you should be able to connect to this copy by visiting
[127.0.0.1:8000](http://127.0.0.1:8000) in your web browser. This way you can
insert your changes without worrying about breaking anything in the production
system.

### Deploy react app´s locally

!!! Note

    This solution is not the best developer experience and needs optimization

As some Apps of the Oeplatform integrate React apps they need to be build using
npm locally. We offer build scripts that can be triggered using django
management commands. For example to build the scenario bundles react app and
deploy it in the django app factsheet you can run the command
`python manage.py build_factsheet_app`. Once done you can access the scenario
bundles app via your locally deployed django instance (see above).

Keep in mind that you now use a bundled version of the react app and all changes
you might want to add to the React jsx components will only show up once you
build the app again. For development this might be a bit clunky but since the
app is deployed inside the django app this enables the React app to use the
django authentication. An alternative that will not be able to use the django
user authentication currently is to deploy the React app alongside the locally
deployed django instance. You can use npm start while being inside the
`factsheet/frontend/` directory in the terminal. To make this work you will have
to change the config.json inside the same directory. In this file you find the
key `"toep": "/"` you'll have to change this `/` value to
`http://127.0.0.1:8000` to point to the django instance currently deployed
locally. If your react test server is still running (`npm start`) you can now
access it at `http://127.0.0.1:3000/scenario-bundles/main`. All changes made to
the React jsx components will now be reflected instantly using live reloading.

## User Management - Setup a test user

To create a dummy user for functionality testing purposes

Run the django management command with arguments. Below you see an example:

    python manage.py create_dev_user "$DEV_USER" "$DEV_USER@mail.com" --password "$DEV_PW" || true

You can also use this script to create a new user. Execute this python code
(either directly in a terminal or from a file)

    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oeplatform.settings")
    django.setup()
    from login.models import myuser
    u = myuser.objects.create_devuser('test','test@mail.com')
    u.set_password('pass')
    u.save()

## Create test tables

You have multiple options to create tables and upload data. We will not explain
the approach using a SQL dump that is imported into the postgresql database. The
easiest approach that will get you started quickly is based on the OEP-Website
UI. The related functionality is part of the `dataedit` app in the django
project.

Before we can get started we have to register the topics where data can be
grouped to. Initially all data is uploaded to the topic `model_draft`. Once it
is published it is moved to another topic e.g. `demand` or `scenario`. You can
use the management command to register our predefined topics:

    python manage.py create_topics

To create and seed the test table using our test dataset you can use the
following command:

    python manage.py create_example_tables

The command will read the example dataset form our representative, minimal
example. Once successfully seeded the database contains the dataset
'example_wind_farm_capacity' in the 'model_draft' topic, including 4 rows of
data and metadata.

### Using the HTTP-API

You can use the http api that is available once you started your local
development server using the `runserver` command. To understand how to use the
api you can have a look at our academy courses but keep in mind that you have to
modify the URL of the api endpoints to you locally running oep instance. You can
to this by changing the beginning of the url from something like
`https://www.oeplatform.org/` to `http://127.0.0.1/`.
[Have a look at this course to get started with the http api.](https://openenergyplatform.github.io/academy/tutorials/01_api/02_api_upload/)

!!! Note

    There are several capabilities which are offered by the API some are aimed on client integration and some are implemented as traditional REST API endpoints. You can find a [openAPI schema here](https://openenergyplatform.github.io/oeplatform/oeplatform-code/web-api/oedb-rest-api/), we are currently working on providing the full list of attributes supported by each endpoint. Until this is done we rely on the academy to provide the key information on how to use the REST-API.

### Using the OEP-Website UI

The OEP-Website includes a features that is called upload wizard internally.
This features usually is used by the user to add datasets to the `model_draft`
topic and can be accessed via the database page. Initially the database is empty
and the topic cards are not visible. You have to navigate to the page manually.
Once you have started your local instance of the OEP you can navigate to this
URL:

    http://127.0.0.1/dataedit/wizard/

There you can create a table, upload data from CSV file, create metadata and
then navigate to the table page. To get started it is okay to just create a
table with minimal requirements by just adding a table name that is all
lowercase and does not include whitespaces, - or any special characters.

## Publish aka move datasets

Once you created your test data you probably want to move your data to any of
the other topics. This functionality is also available via the Website UI and by
using another endpoint of the HTTP-API.

### Via the HTTP-API

There is no tutorial available for this feature. You can send a post request to
the following URL. You need to add your api token to the post request header.
You can have a look on the table create tutorial linked above to understand how
you can do that. In python you can use the package `requests` to perform http
requests.

    http://127.0.0.1/v0/schema/<str:schema>/tables/<str:table>/move/<str:to_schema>/

The URL must include the name of the topic and table you want to move and the
name of the topic you want to move table to. In the future this endpoint will
change because it is part of the publishing process. Moving a table will then
only be possible once the metadata for that table includes an open data license.

### Via the OEP-Website UI

You can navigate to the profile page using your local instance of the OEP
website.

    http://127.0.0.1/user/profile/

There you find a tab called tables. If you include an open data license in the
metadata of your test table you previously create in the `model_draft` topic, a
publish button becomes visible. Once you click it you can select a topic to move
the table to.

You can edit the metadata for a table by visiting the detail page of a table
then click the tab meta information and click the button edit. The license
information should be added to the licenses field of the metadata.

## Import datasets from openenergyplatform.org

Sometimes it is very useful to have actual datasets which are available on the
OEP in your local instance to be able fully reproduce use cases or reproduce
errors.

We offer a
[script](https://openenergyplatform.github.io/oeplatform/oeplatform-code/web-api/oedb-rest-api/)
in the 'script' directory of the oeplatform code project. It is currently a
prototype for doing what is described above. It is not fully tested against all
data types so far so might be error prone.

To use it you must adapt the code and add the information on what datasets you
want to import. Datasets are referenced by schema and table name. It is possible
to import multiple once in one run and you can limit the amount of rows each
dataset should included as some datasets are very large and it is not important
to have the full data for testing use cases.
