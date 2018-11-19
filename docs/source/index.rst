.. OpenEnergyPlatform documentation master file, created by
   sphinx-quickstart on Fri Aug 12 20:13:24 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to OpenEnergyPlatform's documentation!
==============================================

The OpenEnergyPlatform is a website that has three main targets:

   1. Provide a language-independent interface that is a thin layer on top of the OpenEnergyDatabase
   2. Implement an intuitive and easy-to use web interface on top of the OpenEnergyDatabase
   3. Improve the visibility, communication and transparency of results from energy system modelling

Mission statement
*****************

The transition to renewable energy sources is one of the huge goals of the last
few decades. Whilst conventional energy generation provides a constant, generally
available source of electricity, heat and so on, our environment pays a toll.
Contrary, renewable energy generation is less environmentally demanding but more
financially expensive or just locally or inconsistently available.
Guaranteeing a steady and reliable, yet sustainable supply of energy requires
still a lot of thorough research.

Expansion of the energy grid might imply measures that must be communicable in
a transparent way. Hence, results from research of energy system studies should
be publicly available and reproducible. This raises the need for publicly available
data sources.

App: dataedit
*************

One aim ot the OpenEnergyPlatform is the visual and understandable presentation
of such datasets. The underlying OpenEnergyDatabase (OEDB) stores datasets of different
open-data projects. The visual presentation is implemented in the **dataedit** app.

.. toctree::
   :maxdepth: 2

   dataedit


App: api
********

The data stored in the OEDB is also used in several projects. In order to ease
the access to required datasets the OEP provides a RESTful HTTP-interface in
the **api** app:

.. toctree::
   :maxdepth: 2

   api
   api/how_to


App: modelview
**************

Researchers or interested developers that just entered this field might be interested
in an overview which open energy models already exists. This data is collected in
so called fact sheets. Modellers can look through these, add their own models or
enhance existing descriptions using the forms definied in the **modelview** app

.. toctree::
   :maxdepth: 2

   modelview

Other apps are:

App: login
**********

.. toctree::
   :maxdepth: 2

   login

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

