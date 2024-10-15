# Changes to the oeplatform code

## Changes

- Updated oeo in docker image to version 2.5 [(#1878)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1878)

- Fix typo and font-size after tag assignment update [(#1880)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1880)

- Include check for oeo-ext on startup [(#1879)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1879)

## Features

## Bugs

- Updated Dockerfile for sass at theming dir [(#1855)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1855)

- The OEPs table creation process is now atomic to avoid errors: If an error is raised during creation of tables on the OEDB the table object in the django DB is still created. This leads to ghost tables that only exist in django. [(#1886)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1886)

- Fixed wrong calls in dataedit wizard to open collapsed items  [(#1881)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1881)

## Documentation updates

- Added documentation for Design System and Accessibility  [(#1716)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1716)