# Install and setup the Open Energ Platform Application

Below we describe the manual installation of the oeplatform code and infrastructure. 
The installation steps have been proofed on linux and windows for python 3.6 and 3.9.

!!! tip
    We also offer the possibility to use [docker](https://www.docker.com/), to install the oeplatform and additional databases. As the hole setup is preconfigured docker can be used to automatically install the hole infrastructure. 
    
    We provide 2 [docker container images](https://docs.docker.com/get-started/#what-is-a-container-image) (OEP-website and OEP-database). The images are updated & published with each release. They can be pulled from [GitHub packages](https://github.com/OpenEnergyPlatform/oeplatform/pkgs/container/oeplatform).

    [Here you can find instructions on how to install the docker images.](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/docker/USAGE.md)

??? Info "All setps&commands in one list"
   
    1. Get code & install depenecies.
        - `git clone https://github.com/OpenEnergyPlatform/oeplatform.git`
        - `cd oeplatform`
        - `pip -m venv env`
        - `pip install -r requirements.txt`

    2. Install databases & setup connection
        - Setup database 
        - Setup the connection to the database server to the djnago project by adding the credentials in the `oeplatoform/securitysettings.py`

        ??? info "Option 1: Use docker"
            - [Install docker](https://docs.docker.com/get-docker/)
            - while in oeplatform directory `cd docker`
            - `docker compose -f docker-compose.yaml`
            - start docker container

        ??? info "Option 2: Manual database setup"
            - [install manually](manual_db_setup.md)


    3. Run managemant commands
        - `python manage.py migrate`
        - python manage.py alembic upgrade head`
        - `python manage.py collectstatic`

        ??? Info "Sept 3.1: Additional commands" 
            These commands are not relevant if you are setting up oeplatform for the first time. One exception is the mirror command. If you have created some tables manually in the oedb database, you can use the mirror command to register them in the oeplatform.
            
            - `python manage.py mirror`
            - `python manage.py clear_sandbox`
            - `python manage.py clear_peer_reviews --all`


    4. Deploy locally
        - Ckeck if the all connected database servers are running.
        - `python manage.py runserver`
        - Open Browser URL: 127.0.0.1:8000

        - [create a test user.](../dev/developement.md#user-management)

## 1 Setup the repository

Clone the repository locally
    
``` bash
git clone https://github.com/OpenEnergyPlatform/oeplatform.
git oep-website
```

Move to the cloned repository

    cd oep-website

## 2 Setup virtual environment

If you are a windows user, we recommand you use conda because of the dependency on the `shapely` package

    conda env create -f environment.yml

You can also use Python to create the environment

    python -m venv env

If you don't want to use conda, [here](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) you can find instructions for setting up virtual environment

After you have activated your virtual environment, install the required python libraries

    pip install -r requirements.txt

## 3 Databases setup

Currently we use two relational databases to store the oeplatform data: 
 - The oep-django database is our interal database and it is used to store the application related data. This icludes things linke user information, reviews, table names, ... 
 - Our primary database is the oedb (Open Energy Databsae). It is used to store all data the user uploaded. In production it stores multiple terrabyte of data.

### 3.1 How to install the databases
You have two options: 

1. You chose to install the databeses manually by installing PostgreSQL and complete the setup. In this case you can follow our [manual database setup guide](manual_db_setup.md).

2. You can also use our docker based installation to install a container which will automatically setup the two databases. You still have to install docker on your system.
[Here you can find instructions on how to install the docker images.](https://github.com/OpenEnergyPlatform/oeplatform/blob/develop/docker/USAGE.md)

### 3.2 Create the database table structures
Before you can start development, you need to create all the tables in the two PostgreSQL databases. To do this, you can run two management commands. The django command will set up all the structures in the oep_django database and the alembic command will create all the structures in the oedb.

### 3.2.1 Django setup - oep_django

In order to run the OEP website, the django database needs some extra management tables.
We use the django specific migrations. Each django app defines it own migrations that store all changes made to app related tabes. The table structure itself is defines the models for each django app.

    python manage.py migrate

### 3.2.2 Alembic setup - oedb

In order to run the OEP website, the primary database needs some extra management tables.
We use `alembic` to keep track of changes in those tables. To create all tables that are needed, simply type

    python manage.py alembic upgrade head

### 4 Setup the OEO-viewer
!!! note
    This step is not mandatory to run the oeplatform. If you dont include tis setp you can access the oeplatofrm website excluding the ontology pages.

The oeo-viewer is a visualization tool for our OEO ontology and it is under development. To be able to see the oeo-viewer, follow the steps below:

1- Install npm:

- On linux: `sudo apt install npm`

- On MacOS: `brew install node`

- On windows see [here](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

2- Get the ontologie files (full desciption missing) 

3- Build the oeo-viewer:

    cd oep-website/oeo_viewer/client
    npm install
    npm run build

After these steps, a `static` folder inside `oep-website/oeo_viewer/` will be created which includes the results of the `npm run build` command. These files are necessary for the oeo-viewer.

## Next seteps

Have a look at the steps discribed in the [Developement & Collaboration](../dev/developement.md) section.