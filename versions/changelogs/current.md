# Changes to the oeplatform code

## Changes

- Migrate from django version 3.2 to 5.1 [(#1884)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1884)

- Update API responses to be more helpful [(#1912)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1912)

- Removed the outdated & unmaintained references module that was intended to handle bibtex files and store them in a django model [(#1913)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1913).

- Change sparql endpoint for OEKG to use the http post method to match the expected usage [(#1913)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1913).

- Extract header/footer template [(#1914)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1914)

## Features

- Implement new API Endpoint to add new datasets to a scenario bundle -> scenario -> input or output datasets. This eases bulk adding datasets. The API provides extensive error messages. Datasets listed in the scenario topic on the OEP and external datasets registered on the databus.openenergyplatform.org can be used. [(#1914)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1894)

## Bugs

## Documentation updates

- Provide documentation for the OEKG:Scenario Bundle dataset management as described in #1890 [(#1914)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1894)
