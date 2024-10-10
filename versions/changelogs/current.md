# Changes to the oeplatform code

## Changes

- Include check for oeo-ext on startup [(#1879)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1879)

## Features

## Bugs

- The OEPs table creation process is now atomic to avoid errors: If an error is raised during creation of tables on the OEDB the table object in the django DB is still created. This leads to ghost tables that only exist in django. [(#1886)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1886)

## Documentation updates
