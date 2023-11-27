# Scenario Bundles feature

The scenario bundles feature is a response to the complex requirements for the transparent publication of scenarios in a complete and comprehensible manner. Various technologies are used to enable researchers to publish scenarios and any additional information. In addition, existing resources from the open energy platform are used and bundled together. This is intended to increase the visibility of available research work and enable comparability of the scenarios.

## What are Scenario Bundles in detail?

---> Link to compendium.

## Technologies

User Interface

- We offer a modern user interface developed with the REACT library.

Backend & Web-API

- We build on the backend of the Open Energy Platform and use Django to implement functionalities such as saving and deleting scenario bundles and thus enable communication with the database. In addition, Django provides the WEB-API endpoints that are used to create a scenario bundle or query the database using JSON requests, for example.
- A Python integration of the SPARQL query language is used to interact with the Grpah database.

Database

- A graph database is used to store the complex data structure of the scenario bundles in the long term. We use Appache Jenna-Fuseki as a reliable technology.

## Functionalities
