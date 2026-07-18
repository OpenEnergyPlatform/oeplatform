# Complete ontop setup

Download the database JDBC driver for ontop:

- <https://jdbc.postgresql.org/>

Add the file postgresql.jar to this directory.

## Reloading the mapping (dev)

ontop reads `mapping.obda` **only at startup**. If the file changes while the
container is running — a mapping edit, or a `git checkout` that rewrites it —
the container silently keeps serving the old mapping: newly mapped tables return
0 rows in SPARQL and the comparison frontend shows no data.

After **any** change to `mapping.obda` (including branch switches), run:

```sh
./docker/ontop-reload.sh
```

It restarts the `ontop` container, waits for the SPARQL endpoint, and then
verifies that every table mapped in `mapping.obda` on disk is actually served
(row count > 0 via the table-name predicate `oeo:OEO_00000504`).

To only check whether the running container matches the file on disk, without
restarting:

```sh
./docker/ontop-reload.sh --check
```

A `STALE` line means the container loaded an older mapping (restart it) — or the
table exists in the mapping but is empty in Postgres.
