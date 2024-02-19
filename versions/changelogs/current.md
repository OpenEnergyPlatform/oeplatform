# Changes to the oeplatform code

## Changes

- Disable view and edit button on create new page of the scenario bundles  (issue #1576) [(#1577)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1577)
- Fix bug in saving and updating interacting regions  (issue #1576) [(#1597)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1597)

## Features

- implement ready check for ontology app to check for missing oeo release files and guide the user in case of an error [#1457](https://github.com/OpenEnergyPlatform/oeplatform/pull/1547/)

- UI Feature for Publishing Draft Tables: Integrated JavaScript to handle publish actions, including schema selection and confirmation steps, ensuring a seamless user experience.  [(PR#1526)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1526)

- Tooltips for sectors sector divisions and technologies [(PR#1579)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1579)

## Bugs

- Bugfix: Delete a row using the http api leads to server error if table includes not nullable fields [#1581](https://github.com/OpenEnergyPlatform/oeplatform/pull/1581)

- Fix: Users are now redirected to the login page if they attempt to create a new scenario bundle. (Note we will prevent not logged in users to open the create bundle page soon) [(#1595)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1595)

- Fix: Prevent functionality that attempts to connect to an external service and raises errors in the oep server logs. [#1594](https://github.com/OpenEnergyPlatform/oeplatform/pull/1594)
