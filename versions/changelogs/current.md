# Changes to the oeplatform code

## Changes

- Update design sidebar on table detail page [(#1652)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1652)

- Update the code that loads the oeo-related files from local static files. All oeo data is not only loaded when the app is started. Starting the app now takes more time, but offers the advantage that the files do not have to be parsed again. This leads to a significantly faster page load of the ontology pages. [(#1676)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1676)

## Features

- Scenario bundle: The drop-down menu for selecting framework and model factsheets now shows all currently available factsheets instead of retrieving the values from a static list. The factsheets are listed by ‘model_name’ as this is a mandatory field that must be filled in when creating a factsheet. [(#1676)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1676)

## Bugs

## Documentation updates
