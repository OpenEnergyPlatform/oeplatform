# Docker based installation

!!! Warning "🚧"
    This section is still new and might change. The information presented here is tested by the developer and is currently rolled out within our team and close collaborators. Any suggestions are welcome and can be added in this GitHub discussion.

## Introduction

Installing the oeplatform and its infrastructure is a tedious when one wants to setup all the involved components and use them either for development or to deploy them with the goal of operating a dedicated instance for organizations internally or open to the internet. The concept of containerized software helps a lot when developing and also deploying software or even whole infrastructures which may contain several software containers. THe essence of the benefit this brings is the reproducibility due to the container concept. All dependencies which have been installed once successfully can be installed again and any system that supports the container concept which was used will be able to reproduce the build process.

This concept is not exclusive to docker as many parties offer specific container solutions. As docker is rather disseminated and adapted we want to start our route to containerization by providing a docker compose development setup which will enable developers even with low technical literacy to install the oeplatform and apply changes to this local instance of the software infrastructure. We hope that this will enable more contributors to get started with development quickly and learn the details along side the development road.

!!! Note
    We already maintain an docker image of the oeplatform and the OEDB (postgresql database) which is mainly used for CI especially unit and integration testing. These images stays valid for now. The new setup aims for developers and is a more complete version as it introduces services to our docker compose setup which have been missing in the previous version.

## Relevant docker components

Depending on if a docker setup is intended for a production or a development context the included files / services might differ. Sometimes a service is only relevant for development purposes e.g. if we want to have automated reload of assets when developing a frontend to see changes quickly. In production we dont need this module. The following is a general overview of the 3 files most likely be used and especially used in our current setup.

### Dockerfile

Docker files are setup per service and keep all commands for configuration, installation and execution of the service in one place. They are e.g. used to copy directories, install python dependencies which includes creating directories, exposing ports and running commands to execute the software like starting a development server. They also link to the entrypoint script which is described in the next section.

### Docker entrypoints

The entrypoint is a shell script which included all post installation steps of a software. This might include adding specific settings, migrations or setting up test user and data or collecting static files and more. These scripts also also available per service. In some cases a service might not require one of these files.

### Docker compose

Compose is a specific tool provided by docker itself. It can be used in case you want to start more then one software service at a time. This is especially useful if you develop a infrastructure and not only a single software which does not need to communicate with other software services. Composes also created a network so all services can "talk" to each other. The docker compose file list all services whit specific configuration options for each service. This includes info on where the files are copied from which will make up the software, what images are used for other services like databases which are used but not developed as part of the oepaltform project and more.
For development this also offers great tooling as you want to be able to use the container and still edit its contents like source code files and more. Compose offers a bind mount option which will mount you current directory into the container and watch for any file changes. To gether with devcontainer its also possible to use your IDE´s debugger tool and more. To sum this up compose enables us

## Installation

### Docker compose based installation for development purpose

The docker setup is created based on several configuration files and scripts. Together they enable us to install every module of the infrastructure with one single command. This section will give an overview of the setup and also provide commands and any pre-installation steps which will lead to a successful installation of the oeplatform especially and only for development purposes.

#### Docker compose command

!!! Info
    We assume that you already installed these software pieces.

    - [Git](https://git-scm.com/downloads)
    - [Docker](https://docs.docker.com/compose/install/)

Add the following commands into your terminal which supports git and docker compose commands.

    # first close the oeplatform repository
    git clone https://github.com/OpenEnergyPlatform/oeplatform.git

    # navigate into the cloned directory
    docker compose -f docker/docker-compose.dev.yaml


This should print the build process and result in successfully build infrastructure with several containers running. On first start up of the oeplatform container it is likely that you will have to adapt some django settings and or remove some directories in case you have used an existing distribution of the oeplatform code together with previous installations.

Once everything is up and running you are good to start development. This setup also gets you started with some of the main features of the oeplatform as it creates a test user (user "test" and password "pass") and dummy datasets in the database as well as dummy model and framework factsheets and a example scenario bundle.

The docker setups bind mounts your current workspace which is the directory you cloned the oeplatform to. The bind mount enables you to do edits to any code files which will then be picked up by the docker container which is restarting and you will find your edits in the development deployment which you can access in your browser at <http://127.0.0.1:8000>.

#### Remove installations

Using the command below will stop and all containers. Keep in mind that you will detach from the volume which contains all data from you current database, factsheet and scenario bundles as well as all user.

    docker compose -f docker/docker-compose.dev.yaml down

This will only remove the containers not the images or the volumes. If you want to install everything make sure to prune all images and if you also want to remove the data you must also remove the images. You can also do this using docker desktop.

If you want to create them again you can run the first command again. In most cases it is useful to add the --build flag to trigger a new build which will include latest changes. You can add the -D flag to detach the terminal form the container once it is started.

    docker compose -f docker/docker-compose.dev.yaml up --build -d

### Inspect docker containers

To monitor your deployment a very simple way is to use docker desktop. You will find all installed containers and find easy to use options to read the logs or even execute commands. This gives you full insights and control in case some errors and you need to inspect the development server output.
