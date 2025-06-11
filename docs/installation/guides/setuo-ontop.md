# Setup ontop service

The ontop service is mainly use as enabling technology for the quantitative scenario comparison as it enables SPARQL queries on SQL databases using semantic mappings ontop on the "normal" sql like table definition.

## Installation

We offer the pre-configured ontop service as part of the OEP-docker setup for development. It comes with a empty semantic mapping template which can be extended based on the user needs. You still need to download the JDBC database driver to enable connection to the postgresql database OEDB.

Once you downloaded the driver make sure it is available in the ontop config directory and only then build the ontop service using docker.

Download the database JDBC driver for ontop:

- <https://jdbc.postgresql.org/>

Add the file postgresql.jar to this directory.
