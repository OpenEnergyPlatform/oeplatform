# Changes to the oeplatform code

## Changes

- Update test related to oekg queries and avoide using Mocks to keep tests simpler and more realistic by using actual rdflib Graph [(#1980)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1980)

## Features

## Bugs

- Fix the table iri serialized, which now supports external urls stored in the oekg (e.g. When scenarios link to external datasets). External datasets are ignored and return a empty string to avoid exceptions [(#1980)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1980)

## Documentation updates
