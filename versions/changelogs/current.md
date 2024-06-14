# Changes to the oeplatform code

## Changes

- Update design sidebar on table detail page [(#1652)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1652)

- Update the code that loads the oeo-related files from local static files. All oeo data is not only loaded when the app is started. Starting the app now takes more time, but offers the advantage that the files do not have to be parsed again. This leads to a significantly faster page load of the ontology pages. [(#1676)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1676)

- Change the profile tables by improving color contrast, splitting the tables in 2 rows on very large screens and making the whole title visible [(#1706)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1706)

## Features

- Scenario bundle: . [(#1676)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1676)

- Scenario bundle: [(#1704)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1704)

  - It is now possible to add multiple publications to a scenario bundle
  - The drop-down menu for selecting framework and model factsheets now shows all currently available factsheets instead of retrieving the values from a static list. The factsheets are listed by ‘model_name’ as this is a mandatory field that must be filled in when creating a factsheet

- Add toggle functionality to topics table sidebar in order for the table to take 100% of the view width [(#1683)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1683)

- Enhance the OpenPeerReview: New values within a review result (coming from accepted value suggestions) are now also written back to the table metadata. The review now effects the oemetadata for a specific table. [(#1368)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1368)

- Add new embargo area feature: Users can set an embargo period once they create a table or once they publish a table. The embargo period restricts the data access for bot ui & api. [(#1534)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1534)

- Profile page Tables: Add "unpublish" button to published tables. [(#1706)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1706)

- Scenario Bundle: Allow only year for publication date [(#1723)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1723)

## Bugs

- REST-API: Retrieve oemetadata from database instead of comment on table. [(#1703)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1703)

## Documentation updates
