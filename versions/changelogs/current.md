# Changes to the oeplatform code

## Changes


- Enhance embargo area feature (UI & API) [(#1804)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1804)
  - Refactor code
  - The REST API raises an error when creating a table with embargo period but false date time for start/end data
  - Update the table creation http "put" endpoint to handle embargo periods
- Enhances UX by adding a site heading and improve visibility of form controls in the oemetaBuilder tool. [(#1680)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1680)


## Features

- Add the OEP-extended (oeo-ext) feature. It enables users to create new composed units (ontology classes) that extent the units available in the OEO. The feature is implemented as a plugin html form, it can be easily added to any Webpage of the oeplatform. [(#1680)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1680)

## Bugs

## Documentation updates

- Improved OpenAPI documentation of oeplatform REST-API [(#1793)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1793)
