# Changes to the oeplatform code

## Changes

- Added a new docker based development setup which includes the oeplatform website, vite - a javascript bundler and dev server, postgreSQL for the OEDB and django DB as well as a jenna-fuseki databse for the OEKG. We use docker compose the spin up the whole infrastructure and get started with development quickly. This also includes dev-experience enhancements like creting a dev user and a example dataset.
  Currently not all parts fo the infrastructure are covered. Missing are the ONTOP and LOEP services also not all javascript modules are yet connected to vite but will be added later on.
  What is about to be added: We will provide dummy scenario bundles and factsheets for model and frameworks as well as an example sematic mapping which is used by ontop to enable the scenario comparison and its graph based data visualizations. [(#1988)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1988)

- Enhance the robustness of the scenario bundle's React app by fixing errors and warnings from vite. [(#1988)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1988)

- Update test related to oekg queries and avoide using Mocks to keep tests simpler and more realistic by using actual rdflib Graph [(#1980)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1980)

## Features

## Bugs

- Fix the table iri serialized, which now supports external urls stored in the oekg (e.g. When scenarios link to external datasets). External datasets are ignored and return a empty string to avoid exceptions [(#1980)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1980)

- Fix the scenario bundles filter feature and add info banner with additional information in case no filters where set or no results where found with the current filter options. Additionally add a state to the filter options to avoid setting filters the user did not select. [(#2015)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2015)

## Documentation updates

- Add documentation on how to use docker for development [(#1988)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1988)
