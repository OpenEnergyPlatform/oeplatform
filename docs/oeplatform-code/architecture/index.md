# Architecture



# Sturcute of the django project 

Landing page: index
-------------------

The landing page is programmed in **index.html**. It contains a heading,
the main modules in boxes, and further information.

App: dataedit
-------------

One aim of the Open Energy Platform is the visual and understandable
presentation of such datasets. The underlying OpenEnergyDatabase (OEDB)
stores datasets of different open-data projects. The visual presentation
is implemented in the **dataedit** app.


App: api
--------

The data stored in the OEDB is also used in several projects. In order
to ease the access to required datasets the OEP provides a RESTful
HTTP-interface in the **api** app:


App: modelview
--------------

Researchers or interested developers that just entered this field might
be interested in an overview which open energy models already exists.
This data is collected in so called fact sheets. Modellers can look
through these, add their own models or enhance existing descriptions
using the forms definied in the **modelview** app