# Changes to the oeplatform code

## Changes

- All visitors can use metadata builder in standalone version [(#1746)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1746)

- Scenario Bundle Comparison: Harmonize usage of scenario types & study descriptors on bundle & comparison pages. Additionally make all Chips clickable and provide link to oeo class description pages. [#1751](https://github.com/OpenEnergyPlatform/oeplatform/pull/1751)

- The auto-select feature on the scenario bundle/scenario edit page now shows table resources from the scenario topic in the format of: "Metadata Table Title (table_name)" to harmonize the display of table resources also when displaying a bundle. Note: Existing resources must currently be updated manually. [(#1753)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1753)

- Reviewer&Contributor page: calculation of percentage of progress of reviewed fields takes into account empty fields [(#1386)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1386)

## Features

## Bugs

- Open peer review: Fixed several bugs that hindered the user to submit a review, broke the indicators dots that show the review progress & showed badly formatted data on the summary tab [(#1762)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1762)

- Fixed multiple scenario bundle bugs [(#1764)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1764)
  - Fix incorrect rendering of multiple publication years and show None if no data available.
  - Year of publication in scenario bundle detail view now renders only the year
  - Model & framework factsheets are now rendered as clickable chip that links to the detail page of the factsheet. The chip now renders either the acronym or the
    name of the factsheet.

## Documentation updates
