<!--
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: CC0-1.0
-->

# What is this app used for?

The OEKG django app is used to encapsulate functionality to interact with the
OEKG within the OEP. If one needs such functionality in another django app like
`api` then the oekg app should be imported there. New functionality should also
extend the oekg app.

This includes variables and functions to connect to databases (like jenna
fuseki) and to access or edit its content. The main libraries used here are
rdfLib (broadly used in the facthseet app to create scenario bundles) and the
SPARQLWrapper to formulate a Query as a string. The latter approach is more
efficient as it avoids parsing data (like the Graph) to python data types.
