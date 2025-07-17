# Docker based installation

!!! Warning "🚧"
    This section is still new and might change. The information presented here is tested by the developer and is currently rolled out within our team and close collaborators. Any suggestions are welcome and can be added in this GitHub discussion.

!!! Info "Manual installation"
    If you prefer not to use docker or want to get insights into each step of the installation and setup process for the oeplatform please have a look at the [manual installation guide](./installation.md) which also links the [detailed database setup](./manual-db-setup.md).

## Introduction

Installing the oeplatform and its infrastructure is a tedious when one wants to setup all the involved components and use them either for development or to deploy them with the goal of operating a dedicated instance for organizations internally or open to the internet. The concept of containerized software helps a lot when developing and also deploying software or even whole infrastructures which may contain several software containers. THe essence of the benefit this brings is the reproducibility due to the container concept. All dependencies which have been installed once successfully can be installed again and any system that supports the container concept which was used will be able to reproduce the build process.

This concept is not exclusive to docker as many parties offer specific container solutions. As docker is rather disseminated and adapted we want to start our route to containerization by providing a docker compose development setup which will enable developers even with low technical literacy to install the oeplatform and apply changes to this local instance of the software infrastructure. We hope that this will enable more contributors to get started with development quickly and learn the details along side the development road.

!!! Note
    We already maintain an docker image of the oeplatform and the OEDB (postgresql database) which is mainly used for CI especially unit and integration testing. These images stays valid for now. The new setup aims for developers and is a more complete version as it introduces services to our docker compose setup which have been missing in the previous version.

## Relevant docker components

If you want to understand the docker based setup better and read up on what docker components / modules we used to build the development setup you can [read up on the docker compose, docker and docker entrypoint files](../context/docker.md).

## Installation

### Docker compose based installation for development purpose

The docker setup is created based on several configuration files and scripts. Together they enable us to install every module of the infrastructure with one single command. This section will give an overview of the setup and also provide commands and any pre-installation steps which will lead to a successful installation of the oeplatform especially and only for development purposes.

#### Docker compose (optional) environment variables

You can set these environment variablesto override defaults:

- `OEP_DEV_PORT_POSTGRES`: public port to postgres database, defaults to 5432
- `OEP_DEV_PORT_WEB`: public port to web interface, defaults to 8000
- `OEP_DEV_PORT_DEBUGPY`: public port to python debugger, defaults to 5678
- `OEP_DEV_PORT_FUSEKI`: public port to fuseki server, defaults to 3030
- `OEP_DEV_PORT_VITE`: public vite JavaScript server port, defaults to 5173

#### Setup ontop service

The ontop service requires a special database driver which must be [downloaded manually first](./setuo-ontop.md).

#### Docker compose command

!!! Info
    We assume that you already installed these software pieces.

    - [Git](https://git-scm.com/downloads)
    - [Docker](https://docs.docker.com/compose/install/)

    On windows we recommend using WSL2 or a Linux VM as the windows based installation is not tested regularly and often requires additional steps.

Add the following commands into your terminal which supports git and docker compose commands.

    # first close the oeplatform repository
    > git clone https://github.com/OpenEnergyPlatform/oeplatform.git

    # navigate into the cloned directory, on build runs you need to provide you hosts user and group id´s
    > USER_ID=$(id -u) GROUP_ID=$(id -g) docker compose -f docker/docker-compose.dev.yaml up --build

    # From now on you use the command below to startup the setup, but you will have to rebuild
    # the container regularly to pick up latest changes e.g. if a new npm oder pip package was installed.
    > docker compose -f docker/docker-compose.dev.yaml up

#### Using a existing repository

This should print the build process and result in successfully build infrastructure with several containers running. On first start up of the oeplatform container it is likely that you will have to adapt some django settings and or remove some directories in case you have used an existing distribution of the oeplatform code together with previous installations.

Checklist:

- Remove the `oeplatform_data` directory from the docker folder
- Remove any older images and volumes
- Make sure you have a internet connection for the initial setup
- In your oeplatform/securitysettings.py make sure you have the variables from the securitysettings.default.py file available especially the DJANGO_VITE, VITE_DEV_SERVER_URL and the Updated RDF_DATABASES connection credentials are new and you might have to add them.

#### Remove installations

Using the command below will stop and all containers. Keep in mind that you will detach from the volume which contains all data from you current database, factsheet and scenario bundles as well as all user.

    docker compose -f docker/docker-compose.dev.yaml down -v

This will only remove the containers not the images or the volumes. If you want to install everything make sure to prune all images and if you also want to remove the data you must also remove the images. You can also do this using docker desktop.

If you want to create them again you can run the first command again. In most cases it is useful to add the --build flag to trigger a new build which will include latest changes. You can add the -D flag to detach the terminal form the container once it is started.

    docker compose -f docker/docker-compose.dev.yaml up --build -d

### Inspect docker containers

To monitor your deployment a very simple way is to use docker desktop or output the container in your terminal by not using the -d flag when spinning up containers. You will find all installed containers and find easy to use options to read the logs or even execute commands. This gives you full insights and control in case some errors and you need to inspect the development server output.

## Usage

Once everything is up and running you are good to start development. You should now have the following containers running:

- vite (javascript dev server)
- oeplatform-web-dev (OEP)
- postgres-1 (OEDB, Django DB)
- fuseki (OEKG)
- SOON: LOEP (oeo term lookup tool used for ontological annotation)
- SOON: ontop (quantitative data comparison)
- SOON: Docs (mkdocs based documentation website)

### Restart, rebuild and cleanup containers to apply changes

While developing and adding changes you might want to rebuild your docker containers. There are several ways to do this, one is already documented above in the remove installation section. A typical sequence when updating the composed containers:

    # Remove everything, assuming you have a terminal which is at the oeplatform root directory
    docker compose -f docker/docker-compose.dev.yaml down -v

    # Install everything again, don't forget the user id args
    USER_ID=$(id -u) GROUP_ID=$(id -g) docker compose -f docker/docker-compose.dev.yaml up --build

    # Just apply changes to a specific container (see vite as ref to the container name)
    docker compose -f docker/docker-compose.dev.yaml vite down -v
    docker compose -f docker/docker-compose.dev.yaml vite up

### Dummy user and data

This setup also gets you started with some of the main features of the oeplatform as it creates a test user and dummy datasets in the database as well as dummy model and framework factsheets and a example scenario bundle.

- Login with user "test" and password "pass"

### Docker reload on files changes

The docker setups bind mounts your current workspace which is the directory you cloned the oeplatform to. The bind mount enables you to do edits to any code files which will then be picked up by the docker container which is restarting and you will find your edits in the development deployment which you can access in your browser at <http://127.0.0.1:8000>.

This includes python and javascript sourcecode files.

### Working with node/npm (javaScript)

You might want to use node and its package manager npm to install or update package in the package.json file. To do so you should have node installed locally (using node-version-manager "nvm") and install new packages using the npm cli. You can also install them directly in the docker container using the "excec" option.

    npm install "package-name" --save


Then you build the vite container, it will pickup the changes in the package.json / package-lock.json and update the container node_modules. See also more info on the [node.js aka JavaScript setup](./nodejs.md).

    docker compose -f docker/docker-compose.dev.yaml vite up --build
