# Docker Usage

> Works for Linux & MacOS (probably). It is tested with Linux.
> You also need a working Docker installation and some basic knowledge about command lines. 

This is a short introduction into the usage of Docker with Open Energy Platform (OEP). We provide **two** seperate images for the OEP, a database image and a application image. The database image prepares a ready-to-use database for the OEP and is an extension to a common PostgreSQL docker image. The application image contains the OEP and connects to a container running the database image. There are some additional resources at *Further Information* for an more in-depth understanding.

## Usages

### Full Docker Installation

This can be used, if you just want to host your own OEP installation or test API scipts or something similar, that should not be done with the public instance.

TODO: Write this chapter

### Database Container with local installation

This can be used, if you want to use a local installation for development and don't want to mess with the database setup (which should be the normal case).

We start the database container and expose the database to our host. Afterwards, we prepare the `securitysettings.py` with the correct credentials and migrate the database to our current branch.

```sh
docker run -p "5432:5432" -v "$(pwd)/oeplatform_data:/var/lib/postgresql/data" ghcr.io/openenergyplatform/oeplatform-postgres:latest
```

This command starts a container with the `oeplatform-postgres` docker image. It automagically creates the needed tables. The database saves its information at your current working directory within the `oeplatform_data` folder. It also tunnels the PostgreSQL port to your local machine to make it accessable from your host. This enables you to connect your OEP instance to your machine.

Connecting the OEP to the database container is similar to any other PostgreSQL instance. You need to adapt the `securitysettings.py` to the correct values **OR** set the correct environment, if you use the default values.

Description | Value | Environment Value 
-|-|-
|Django Database Name|oep_django|`OEP_DJANGO_NAME`
|Local Database Name|oedb|`LOCAL_DB_NAME`
|Database User|postgres|`OEP_DJANGO_USER`,`LOCAL_DB_USER`
|Database Password|postgres|`OEP_DB_PW`,`LOCAL_DB_PASSWORD`
|Database Host|localhost|`OEP_DJANGO_HOST`,`LOCAL_DB_HOST`
|Database Port|5432|`LOCAL_DB_PORT`

Afterwards, the application should be able to connect to the empty databases. You need to run the migrations as usual. The following commands are a short summary from the installation instructions.

```sh
# Make sure, you expose the environment correctly to run migrations.

export OEP_DJANGO_USER=postgres
export OEP_DB_PW=postgres
export OEP_DJANGO_HOST=localhost
export OEP_DJANGO_NAME=oep_django
export LOCAL_DB_USER=postgres
export LOCAL_DB_PASSWORD=postgres
export LOCAL_DB_NAME=oedb
export LOCAL_DB_HOST=localhost

# Running Migrations
python manage.py alembic upgrade head
python manage.py migrate
```

If the PostgreSQL container gets stopped, it can be recreated with the existing `oeplatform_data` folder. You do **NOT** need to run migrations on an existing folder except a changed application version.

If you followed this documentation, you can skip the entire `Setup Your Database` chapter. You already did this and your application is ready to be started.

## Tasks

### Start Database On Existing Data

+ Make sure, `oeplatform_data` exists in your working directory.
+ Run `docker run -p "5432:5432" -v "$(pwd)/oeplatform_data:/var/lib/postgresql/data" ghcr.io/openenergyplatform/oeplatform-postgres:latest`.

### Reset Database

+ Stop Database
+ Remove `oeplatform_data` folder from our working directory
+ Start Database
    + Database will recreate all needed tables
    + You need to reapply the migrations

## Further Information

+ [Image vs Container](https://stackoverflow.com/questions/23735149/what-is-the-difference-between-a-docker-image-and-a-container)
