# Changes to the oeplatform code

## Changes

## Features

## Bugs

- If an error is raised during creation of tables on the OEDB the table object in the django DB is still created. This leads to ghost tables that only exist in django. By first creating the OEDB table the checks are performed first. This approach in still enables only creating one table in one of the databases. [(#1886)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1886)

## Documentation updates
