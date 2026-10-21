#!/usr/bin/env sh
set -e

# The stamp lives INSIDE node_modules on purpose. node_modules is a named
# volume while the repo is a bind mount, so a stamp at the repo root can claim
# a dependency tree it has never seen: the volume survives an image rebuild
# (docker only seeds a named volume while it is empty), and a stamp written on
# the host then silences this check against a node_modules that predates the
# lockfile. That is how the container ended up running vite 8.0.16 against a
# lockfile pinning 8.0.13, which breaks @elastic/eui's dynamically imported
# icon chunks in the dep optimizer.
STAMP="node_modules/.node_modules_stamp"
# compute the current lockfile checksum
checksum=$(md5sum package-lock.json | awk '{print $1}')


# if modules missing/empty, or stamp missing, or deps changed → reinstall
if [ ! -d node_modules ] \
   || [ -z "$(ls -A node_modules)" ] \
   || [ ! -f "$STAMP" ] \
   || [ "$(cat "$STAMP")" != "$checksum" ]; then
  echo "⟳  installing/updating dependencies…"
  npm ci
  echo "$checksum" > "$STAMP"
  # npm ci wipes node_modules, so any prebundled deps belong to the old tree.
  rm -rf node_modules/.vite
fi

# hand off to the original CMD (e.g. `npm run dev …`)
exec "$@"
