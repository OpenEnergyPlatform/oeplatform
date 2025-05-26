# Relevant docker components

Depending on if a docker setup is intended for a production or a development context the included files / services might differ. Sometimes a service is only relevant for development purposes e.g. if we want to have automated reload of assets when developing a frontend to see changes quickly. In production we dont need this module. The following is a general overview of the 3 files most likely be used and especially used in our current setup.

## Dockerfile

Docker files are setup per service and keep all commands for configuration, installation and execution of the service in one place. They are e.g. used to copy directories, install python dependencies which includes creating directories, exposing ports and running commands to execute the software like starting a development server. They also link to the entrypoint script which is described in the next section.

## Docker entrypoints

The entrypoint is a shell script which included all post installation steps of a software. This might include adding specific settings, migrations or setting up test user and data or collecting static files and more. These scripts also also available per service. In some cases a service might not require one of these files.

## Docker compose

Compose is a specific tool provided by docker itself. It can be used in case you want to start more then one software service at a time. This is especially useful if you develop a infrastructure and not only a single software which does not need to communicate with other software services. Composes also created a network so all services can "talk" to each other. The docker compose file list all services whit specific configuration options for each service. This includes info on where the files are copied from which will make up the software, what images are used for other services like databases which are used but not developed as part of the oepaltform project and more.
For development this also offers great tooling as you want to be able to use the container and still edit its contents like source code files and more. Compose offers a bind mount option which will mount you current directory into the container and watch for any file changes. To gether with devcontainer its also possible to use your IDE´s debugger tool and more. To sum this up compose enables us
