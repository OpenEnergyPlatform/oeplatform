# Changes to the oeplatform code

## Changes

- Reworked user group section (part of the profile page). User can create and manage groups that can be added to tables and in the future also to scenario bundles [(#1611)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1611).
  - Also includes updates to the profile tables section where a reworked UI was implemented for #1607.
  - Fix broken autocomplete & client side validate user input when assigning groups or users to table permissions.
  - requirements updated for python 3.10
  - read knowledge graph endpoints from securitysettings.py

## Features

- Add NFDI to our list of Partners [(#1605)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1605).

- Add feature to reset a api token via the profile/settings page [(#1637)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1637)

- Add Pagination to user tables section in the profile page [(#1655)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1655)

## Bugs

- Bugfix: Adding tags if metadata is empty does not result in a server error anymore. [(#1528)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1528)

- OEMetaBuilder: Readd missing autocomplete functionality that was not added after the oemetadata schema update for metadata version 0.1.6 [(#1608)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1608)

- Fix migration dataedit 0033: Provide default value for not nullable oemetdata field. [(1635)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1635)

- Docker: docker-entrypoint.sh wasn't running compression of stylesheets on startup [(#1627)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1627)

- Update requirements: Fix drf pip version to v3.14 to avoid [django-reset-framework issue](https://github.com/encode/django-rest-framework/issues/9300) [(1630)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1630)

- Include oeo in oeplatform docker image [(#1631)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1631)

## Documentation updates

New section!

- Update the REST-API page of the documentation [(#1636)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1636):
  - It is currently work in progress and will be updated within the next couple months.
  - This update adds more context and links to the academy api tutorials.
- Update docker documentation [(#1644)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1644)
