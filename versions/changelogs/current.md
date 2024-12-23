# Changes to the oeplatform code

## Changes

- Migrate from django version 3.2 to 5.1 [(#1884)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1884)

- Update API responses to be more helpful [(#1912)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1912)

- Removed the outdated & unmaintained references module that was intended to handle bibtex files and store them in a django model [(#1913)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1913).

- Change sparql endpoint for OEKG to use the http post method to match the expected usage. The OEKG API is also extended to return data in common rdf/graph formats like tutle or json ld [(#1928)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1928).

- Extract header/footer template [(#1914)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1914)

## Features

## Bugs

## Documentation updates

- Updated documentation to simplify usage of vendor software swagger ui and update the documentation on scenario bundles. Add documentation on how to use the updated OEKG web API [(#1928)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1928).
