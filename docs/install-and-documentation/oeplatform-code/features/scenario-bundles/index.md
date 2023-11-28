
# Scenario Bundles feature

The scenario bundles feature is a response to the complex requirements for the transparent publication of scenarios in a complete and comprehensible manner. Various technologies are used to enable researchers to publish scenarios and any additional information. In addition, existing resources from the open energy platform are used and bundled together. This is intended to increase the visibility of available research work and enable comparability of the scenarios.

## What are Scenario Bundles in detail?

Please continue reading [here](https://openenergyplatform.github.io/organisation/family_members/templates-and-specification/scenario-bundles/).

## Technologies

User Interface

- We offer a modern user interface developed with the REACT library.

Backend & Web-API

- We build on the backend of the Open Energy Platform and use Django to implement functionalities such as saving and deleting scenario bundles and thus enable communication with the database. In addition, Django provides the WEB-API endpoints that are used to create a scenario bundle or query the database using JSON requests, for example.
- A Python integration of the SPARQL query language is used to interact with the Grpah database.

Database

- A graph database is used to store the complex data structure of the scenario bundles in the long term. We use Appache Jenna-Fuseki as a reliable technology.

## Functionalities

## Code Documentation

### Django view for the scenario bundles

!!! note
    Some of the information on this page may be changed in the future. To review the most recent information, please revisit.

`def create_factsheet(request, *args, **kwargs):`

#### ::: factsheet.views.create_factsheet

`def update_factsheet(request, *args, **kwargs):`

#### ::: factsheet.views.update_factsheet

`def factsheet_by_id(request, *args, **kwargs):`

#### ::: factsheet.views.factsheet_by_id

`def delete_factsheet_by_id(request, *args, **kwargs):`

#### ::: factsheet.views.delete_factsheet_by_id

`def add_entities(request, *args, **kwargs):`

#### ::: factsheet.views.add_entities

`def delete_entities(request, *args, **kwargs):`

#### ::: factsheet.views.delete_entities

`def update_an_entity(request, *args, **kwargs):`

#### ::: factsheet.views.update_an_entity

`def query_oekg(request, *args, **kwargs):`

#### ::: factsheet.views.query_oekg

`def get_entities_by_type(request, *args, **kwargs):`

#### ::: factsheet.views.get_entities_by_type
