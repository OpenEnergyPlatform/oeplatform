# Changes to the oeplatform code

## Features

- Add a new OEO search page for simple search and browsing of OEO entities
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Add interactive parent/child hierarchy navigation and IRI copy functionality
  to entity detail pages
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- **Implemented Cross-Navigation:** Users can now seamlessly switch from an
  Entity Detail page to the OEO Viewer with the specific term and type
  pre-selected via URL parameters.
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- **OEO Viewer Enhancements
  [(#2238)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2238):**
  - Added a **"Share View"** button to copy a permanent link to the current
    visualization configuration.
  - Added a **"Copy Term IRI"** button to easily retrieve the stable OEP
    identifier.
  - Implemented Toast notifications for user feedback on copy actions.
  - Added responsive layout logic to switch between Split View (Desktop) and
    Accordion View (Mobile).

## Changes

- Reworked the former OEO Class pages into OEO Entity pages, now supporting
  details for Classes, Properties, and Individuals
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Integrated NFDI4Energy Terminology Service Suite (TSS) React widgets for
  standardized search, metadata, and relations displays
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Improved IRI resolution to seamlessly handle and route external/imported
  ontology terms (e.g., OBO Foundry)
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Implemented client-side React routing (SPA) for seamless transitions between
  search results and entity details
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Reworked the OEO Viewer using React and the
  [TSS Widgets library](https://ts4nfdi.github.io/terminology-service-suite/comp/latest/?path=/docs/overview--docs),
  providing enhanced usability.
  [(#2222)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2222)
- Shifted OEO Viewer data retrieval to the
  [TIB Terminology Service](https://terminology.tib.eu/ts) (OLSv4 backend),
  significantly reducing future maintenance efforts by leveraging
  NFDI-maintained widgets.
  [(#2222)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2222)
- **UI/UX Polish
  [(#2238)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2238):**
  - Updated visual hierarchy in Metadata widgets (Bold Entity Names, styled
    Ontology Badges) to improve readability.
  - Added "How to Use" collapsible guide to the OEO Viewer.
  - Added links to external resources (Technoportal, TIB TS) for advanced users.

## Removed

- Removed the previous custom backend and frontend implementation for the OEO
  Class / IRI pages
  [(#2234)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2234)
- Removed the legacy custom backend and frontend implementation of the OEO
  Viewer. [(#2222)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2222)

## Bugs

- Fixed an issue related to the Bootstrap vs EUI conflicts which led to strange
  styling when using the autocomplete widget.
  [(#2238)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2238)
- Fixed Graph View responsiveness in the OEO Viewer by overriding hardcoded TSS
  library dimensions.
  [(#2238)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2238)
- Fixed race conditions in URL state management to ensure deep links initialize
  correctly on page reload.
  [(#2238)](https://github.com/OpenEnergyPlatform/oeplatform/pull/2238)

## Documentation updates

## Dependencies
