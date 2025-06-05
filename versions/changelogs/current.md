# Changes to the oeplatform code

## Changes

- Added a new docker based development setup which includes the oeplatform website, vite - a javascript bundler and dev server, postgreSQL for the OEDB and django DB as well as a jenna-fuseki databse for the OEKG. We use docker compose the spin up the whole infrastructure and get started with development quickly. This also includes dev-experience enhancements like creting a dev user and a example dataset.
  Currently not all parts fo the infrastructure are covered. Missing are the ONTOP and LOEP services also not all javascript modules are yet connected to vite but will be added later on.
  What is about to be added: We will provide dummy scenario bundles and factsheets for model and frameworks as well as an example sematic mapping which is used by ontop to enable the scenario comparison and its graph based data visualizations. [(#1988)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1988)

- Enhance the robustness of the scenario bundle's React app by fixing errors and warnings from vite. [(#1988)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1988)

- Update test related to oekg queries and avoide using Mocks to keep tests simpler and more realistic by using actual rdflib Graph [(#1980)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1980)

- Enhance docker based dev setup by adding loep (lookup) service which enables the annotation feature in the oemetabuilder [(#2014)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2014)

- Refactor plain django based login system and replace its core by django allauth with custom OEP-styles thanks to @bmlancien [(#1896)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1896)

- Rework the navigation bar and promote each section and feature which can be linked individually as well as link to more external content which is close to the OEP. This change should help users to find specific features [(#2024)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2024)

## Features

- Add NFDI AAI based login system enabled by KIT´s RegApp for Single Sign on. This enables institutional and ORCID based social login additionally to the oeplatform internal login system [(#1896)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1896)

- Avoid caching scenario bundle related http-api endpoints to keep data up to date. This effects the scenario top tables list as well as the model & framework factsheet list endpoints [(#2021)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2021)

## Bugs

- Fix the table iri serialized, which now supports external urls stored in the oekg (e.g. When scenarios link to external datasets). External datasets are ignored and return a empty string to avoid exceptions [(#1980)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1980)

- Fix the scenario bundles filter feature and add info banner with additional information in case no filters where set or no results where found with the current filter options. Additionally add a state to the filter options to avoid setting filters the user did not select and implement the reset filter button. [(#2015)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2015)

- Fix bugs in the table creation which left table artifacts hanging & a bug which occurred when user add a tag to a table without existing metadata[(#1896)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1896)

- Fixed a bug in the OEMetaBuilder tool which lead to incomplete editable metadata properties in the editor and incomplete auto-added values in the data schema section [(#1896)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1896)

- Fix previously working functionality which extracts and show the table title form metadata instead of the filename when browsing table data. [(#2022)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2022)

## Documentation updates

- Add documentation on how to use docker for development [(#1988)](https://github.com/OpenEnergyPlatform/oeplatform/pull/1988)
