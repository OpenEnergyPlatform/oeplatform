#!/usr/bin/env sh
set -e

STAMP=".node_modules_stamp"
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
fi

# hand off to the original CMD (e.g. `npm run dev …`)
exec "$@"
