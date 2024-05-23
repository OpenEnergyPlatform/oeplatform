# Changes to the oeplatform code

## Changes

- Update design sidebar on table detail page [(#1652)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1652)

- Update the code that loads the oeo-related files from local static files. All oeo data is not only loaded when the app is started. Starting the app now takes more time, but offers the advantage that the files do not have to be parsed again. This leads to a significantly faster page load of the ontology pages. [(#1676)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1676)

## Features

- Enhance the OpenPeerReview: New values within a review result (coming from accepted value suggestions) are now also written back to the table metadata. The review now effects the oemetadata for a specific table. [(#1368)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1368)

## Bugs

## Documentation updates
