# Changes to the oeplatform code

## Changes

## Features

- Add NFDI to our list of Partners [(#1605)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1605).

## Bugs

- Bugfix: Adding tags if metadata is empty does not result in a server error anymore. [(#1528)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1528)

- OEMetaBuilder: Readd missing autocomplete functionality that was not added after the oemetadata schema update for metadata version 0.1.6 [(#1608)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1608)

- Docker: docker-entrypoint.sh wasn't running compression of stylesheets on startup [(#1627)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1627)

- Update requirements: Fix drf pip version to v3.14 to avoid [django-reset-framework issue](https://github.com/encode/django-rest-framework/issues/9300) [(1630)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1630)

- Include oeo in oeplatform docker image [(#1631)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1631)

## Documentation updates

New section!

- Update the REST-API page of the documentation [(#1632)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1632):
  - It is currently work in progress and will be updated within the next couple months.
  - This update adds more context and links to the academy api tutorials.
