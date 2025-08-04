<!--
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Eike Broda <https://github.com/ebroda>
SPDX-FileCopyrightText: 2025 Jonas H <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Kirann Bhavaraju <https://github.com/KirannBhavaraju> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Ludwig Hülk <https://github.com/Ludee> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Ludwig Hülk <https://github.com/Ludee> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Pierre Francois <https://github.com/Bachibouzouk> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Santosch Mutyala <https://github.com/smutyala1at>
SPDX-FileCopyrightText: 2025 Tu Phan Ngoc <RL-INSTITUT\tuphan.ngoc@rli-nb-65.rl-institut.local> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Hofmann <https://github.com/christian-rli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 chrwm <https://github.com/chrwm> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Lara Christmann <https://github.com/solar-c> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Mirjam Stappel <https://github.com/stap-m> © Fraunhofer IEE
SPDX-FileCopyrightText: 2025 user <https://github.com/Darynarli> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Vismaya Jochem <https://github.com/vismayajochem> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# Changes to the oeplatform code

## Changes

- Grouping in the opening window for indexed fields on the summary page ([#1946](https://github.com/OpenEnergyPlatform/oeplatform/pull/1946))
- Indexed fields are numbered starting from 1 ([#1946](https://github.com/OpenEnergyPlatform/oeplatform/pull/1946))
- Removing contributor tab from peer review ([#2026](https://github.com/OpenEnergyPlatform/oeplatform/pull/2026))
- Opening windows for indexed fields an subcategories in opr ([#2026](https://github.com/OpenEnergyPlatform/oeplatform/pull/2026))
- Dividing the review functionality into 7 javaScript modules, the main module is the new entry point which is connected to vite and djnago staticfiles ([#1965](https://github.com/OpenEnergyPlatform/oeplatform/pull/1965))
- Add javaScript modules: main for connecting logic as entrypoint; navigation for switching between fields/tabs; opr_reviewer_logic for checking if review is complete; peer_review for main review logic; state_current_review for getting certain values from review; summary for review summary ([#1965](https://github.com/OpenEnergyPlatform/oeplatform/pull/1965))
- Change main views function for metadata v2 structure ([#2026](https://github.com/OpenEnergyPlatform/oeplatform/pull/2056))

## Features

- Add Dataset rest-api and metadata based concept as specified in oemetadata / frictionless ([#2071](https://github.com/OpenEnergyPlatform/oeplatform/pull/2071))

  - Ressource metadata is stored for each created table.
  - Dataset objects can be listed, created, edited and existing tables can be assigned as resource
  - Datasets and assigned Ressources are stored in the django database using a m:n relation with tables to read the oemetadata.
  - Rest api implementation

## Bugs

## Removed

## Documentation updates
