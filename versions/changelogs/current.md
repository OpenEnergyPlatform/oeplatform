# Changes to the oeplatform code

## Changes

- Open-Peer-Review [(#1800)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1800)
 - Removed state suggestions for accepted fields. 
 - Updated recursive_update function to handle deletion and overwriting of suggested/rejected values.
 - Removed value requirements for "deny" buttons in certain actions.

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

## Documentation updates
