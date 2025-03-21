# Changes to the oeplatform code

## Changes

- Migrate from django version 3.2 to 5.1 [(#1884)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1884)

- Update API responses to be more helpful [(#1912)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1912)

- Removed the outdated & unmaintained references module that was intended to handle bibtex files and store them in a django model [(#1913)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1913).

- Change sparql endpoint for OEKG to use the http post method to match the expected usage [(#1913)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1913).

- Extract header/footer template [(#1914)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1914)

- Open-Peer-Review [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
 - Removed state suggestions for accepted fields. 
 - Updated recursive_update function to handle deletion and overwriting of suggested/rejected values.
 - Removed value requirements for "deny" buttons in certain actions.


- Change sparql endpoint for OEKG to use the http post method to match the expected usage. The OEKG API is also extended to return data in common rdf/graph formats like tutle or json ld [(#1928)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1928).


Update the oemetadata sectionin 'dataedit/static/metaEdit/' to enable metadata editing for the new oemetadata v2. Additionally, introduce more extensive category tabs to enhance the metaBuilder UI [(#1914)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1914).

## Features

- Open-Peer-Review [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
 - Added a new button Save Comments for adding comments to rejected fields.
 - Display functionality for add_comment fields was implemented for rejected items.
 - Enabled active ok button functionality without page reload for unreviewed fields.


## Bugs

- Open-Peer-Review [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800):
 - Fixed bug with displaying the same field twice.
 - Addressed an issue with missing fields for "suggest/deny" and status in specific contexts.
 - Disabled unnecessary "ok/deny" buttons for reviewer-rejected fields.
 - Corrected metadata updates by removing functionality for rejected fields in PeerReview & Table tables.
 - Resolved issue where the status label showed "Missing" instead of "Pending" on submission.
 - Fixed display issues with empty fields when there were two statuses. 

- Fix outdated service url to send requests to the LEOP from the oemetaBuilder and oeo-extended features[(#1938)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1938).


## Documentation updates

- Updated documentation to simplify usage of vendor software swagger ui and update the documentation on scenario bundles. Add documentation on how to use the updated OEKG web API [(#1928)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1928).
