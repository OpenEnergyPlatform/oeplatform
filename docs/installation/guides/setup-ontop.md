# Setup ontop service

The ontop service is mainly use as enabling technology for the quantitative
scenario comparison as it enables SPARQL queries on SQL databases using semantic
mappings ontop on the "normal" sql like table definition.

## Installation

We offer the pre-configured ontop service as part of the OEP-docker setup for
development. It comes with a empty semantic mapping template which can be
extended based on the user needs.

The ontop image is self-provisioning — the PostgreSQL JDBC driver, the ontology
(`ontology.owl`) and the mapping (`mapping.obda`) are all baked into the image
at build time. No files need to be placed or downloaded manually.

- The JDBC driver is fetched from Maven Central during the build. Pin a version
  with `--build-arg JDBC_VERSION=x.y.z` (default: 42.7.3).
- The database connection is configured through environment variables (in
  `oep.env` / `.env`), so there is no `ontop.properties` file to create:

  ```sh
  ONTOP_DB_URL=jdbc:postgresql://postgres:5432/oedb
  ONTOP_DB_USER=<postgres user>
  ONTOP_DB_PASSWORD=<postgres password>
  ```

To customise the mapping, edit `docker/serviceConfigs/ontop/mapping.obda` and
rebuild, or bind-mount your own file over `/opt/ontop-config/mapping.obda`.
