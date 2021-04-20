************
Scenario API
************

This API is built on RDF factories, which are comparable to django models. Each factory has a collection of fields.
Let's look at the Person factory:

.. autoclass:: modelview.rdf.factory.Person
    :members:

This factory has three fields (excluding `classes`): `affiliation`, `first_name`, `last_name`. Each of them relates to one
rdf:Property, which is identified by the respective URL (`field.rdf_name`).

.. autoclass:: modelview.rdf.field.Field

Given a subject `:subject` a field `f` can be transformed into an rdf triple by

.. code-block::

    ":subject {p} {o}".format(p=f.rdf_name, o=v)

for each `v` in `f.values`.

A `POST` request to to a resource expects a data dictionary that has a `graph` field that contains an RDF-graph representing the
new structure. Following is a list of all available factories with all their fields (and the respective IRIs):



Factories
#########

.. automodule:: modelview.rdf.factory
  :members:

