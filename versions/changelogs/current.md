# Changes to the oeplatform code

## Changes

- Enhance embargo area feature (UI & API) [(#1804)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1804)

  - Refactor code
  - The REST API raises an error when creating a table with embargo period but false date time for start/end data
  - Update the table creation http "put" endpoint to handle embargo periods

- Enhances UX by adding a site heading and improve visibility of form controls in the oemetaBuilder tool. [(#1680)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1680)

- Enhance the ontology pages, remove the modules page and fully rework the about page and oeo download capabilities. Additionally add the oeox and make its URIs available, also add more cases where a Http404 is raised to make [(#1807)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1807)

- Update the OpenEnergyFamily group picture on the about page [(#1816)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1816)
- Update existing ontology layout [(#1850)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1850)

- Add the page header bar (name of feature and on page navigation below nav bar) to data upload wizard & oeo-viewer pages [(#)](https://github.com/OpenEnergyPlatform/oeplatform/pull/).

## Features

- Add the OEP-extended (oeo-ext) feature. It enables users to create new composed units (ontology classes) that extent the units available in the OEO. The feature is implemented as a plugin html form, it can be easily added to any Webpage of the oeplatform. [(#1680)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1680)

- Add error message display to oeox-plugin view. [(#1812)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1812)

## Bugs

- Added missing setting for Authorization of users in API requests [(#1830)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1830)

- Added check to ensure table name is valid before creation in API [(#1834)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1834)

## Documentation updates

- Improved OpenAPI documentation of oeplatform REST-API [(#1793)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1793)
- Updated documentation for docker to include how to restart oeplatform [(#1830)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1830)
