# Changes to the oeplatform code

## Changes

- Removed state suggestions for accepted fields. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Updated recursive_update function to handle deletion and overwriting of suggested/rejected values. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Removed value requirements for "deny" buttons in certain actions. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)

## Features

- Added a new button Save Comments for adding comments to rejected fields. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Display functionality for add_comment fields was implemented for rejected items. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Enabled active ok button functionality without page reload for unreviewed fields. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)

- divide metadata builder flow into subsections [(#1747)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1747)


## Bugs

- Fixed bug with displaying the same field twice. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Addressed an issue with missing fields for "suggest/deny" and status in specific contexts. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Disabled unnecessary "ok/deny" buttons for reviewer-rejected fields. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Corrected metadata updates by removing functionality for rejected fields in PeerReview & Table tables. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Resolved issue where the status label showed "Missing" instead of "Pending" on submission. [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
- Fixed display issues with empty fields when there were two statuses. 

- Updated oeo in docker image to version 2.5 [(#1878)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1878)

- Fix typo and font-size after tag assignment update [(#1880)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1880)

- Include check for oeo-ext on startup [(#1879)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1879)

- Updated Dockerfile for sass at theming dir [(#1855)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1855)

- Migrate from django version 3.2 to 5.1 [(#1884)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1884)

- Update API responses to be more helpful [(#1912)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1912)

- Removed the outdated & unmaintained references module that was intended to handle bibtex files and store them in a django model [(#1913)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1913).

- Change sparql endpoint for OEKG to use the http post method to match the expected usage  [(#1913)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1913).

- Extract header/footer template [(#1914)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1914)

## Features

## Bugs



## Documentation updates
