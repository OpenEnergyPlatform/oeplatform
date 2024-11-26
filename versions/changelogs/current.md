# Changes to the oeplatform code

## Changes

- Migrate from django version 3.2 to 5.1 [(#1884)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1884).

## Features

## Bugs

- upload wizard: only upload mapped columns to allow autoincremented id

- Updated Dockerfile for sass at theming dir [(#1855)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1855)

- The OEPs table creation process is now atomic to avoid errors: If an error is raised during creation of tables on the OEDB the table object in the django DB is still created. This leads to ghost tables that only exist in django. [(#1886)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1886)

- Fixed wrong calls in dataedit wizard to open collapsed items  [(#1881)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1881)

## Documentation updates
