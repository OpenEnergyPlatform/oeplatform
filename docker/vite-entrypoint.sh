#!/usr/bin/env sh
set -e

# if there's no node_modules (or it's empty), install from package*.json
if [ ! -d node_modules ] || [ -z "$(ls -A node_modules)" ]; then
  echo "⟳  installing dependencies…"
  npm ci
fi

# now hand off to whatever CMD you passed in
exec "$@"
