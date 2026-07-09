#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Restart the dev ontop container and verify that what it serves matches
# docker/serviceConfigs/ontop/mapping.obda.
#
# ontop reads the OBDA mapping ONLY at startup: after a branch switch or a
# mapping edit, a running container silently keeps serving the old mapping
# (newly mapped tables return 0 rows). Run this after any mapping change.
#
# Usage:
#   ./docker/ontop-reload.sh            restart, wait for the endpoint, verify
#   ./docker/ontop-reload.sh --check    verify only (no restart)
#
# Environment overrides: ONTOP_CONTAINER (default: ontop),
# ONTOP_ENDPOINT (default: http://localhost:8080/sparql), ONTOP_TIMEOUT (120s).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${ONTOP_CONTAINER:-ontop}"
ENDPOINT="${ONTOP_ENDPOINT:-http://localhost:8080/sparql}"
MAPPING="$SCRIPT_DIR/serviceConfigs/ontop/mapping.obda"
# table-name predicate emitted by every row anchor (see oekg/registry)
TABLE_PRED="https://openenergyplatform.org/ontology/oeo/OEO_00000504"
TIMEOUT="${ONTOP_TIMEOUT:-120}"

if [[ "${1:-}" != "--check" ]]; then
  echo "Restarting '$CONTAINER'..."
  docker restart "$CONTAINER" >/dev/null
fi

printf 'Waiting for %s ' "$ENDPOINT"
deadline=$((SECONDS + TIMEOUT))
until curl -sf -o /dev/null --data-urlencode 'query=ASK {}' "$ENDPOINT"; do
  if ((SECONDS >= deadline)); then
    printf '\nERROR: endpoint not answering after %ss\n' "$TIMEOUT" >&2
    exit 1
  fi
  printf '.'
  sleep 3
done
printf ' up.\n'

# Tables the mapping file on disk maps (FROM "schema"."table" in the source SQL).
mapfile -t expected < <(grep -oE 'FROM[[:space:]]+"[^"]+"\."[^"]+"' "$MAPPING" |
  sed -E 's/.*\."([^"]+)"$/\1/' | sort -u)
if ((${#expected[@]} == 0)); then
  echo "ERROR: no mapped tables found in $MAPPING" >&2
  exit 1
fi

# Tables the running endpoint actually serves, with row counts.
query="SELECT ?t (COUNT(?s) AS ?c) WHERE { ?s <$TABLE_PRED> ?t } GROUP BY ?t ORDER BY ?t"
csv="$(curl -sf -H 'Accept: text/csv' --data-urlencode "query=$query" "$ENDPOINT")"

status=0
echo "Mapped tables (mapping.obda on disk vs SPARQL endpoint):"
for t in "${expected[@]}"; do
  count="$(printf '%s\n' "$csv" | tr -d '\r' | awk -F, -v t="$t" '$1 == t {print $2}')"
  if [[ -n "${count:-}" && "$count" != "0" ]]; then
    printf '  OK    %-45s %s rows\n' "$t" "$count"
  else
    printf '  STALE %-45s not served (0 rows)\n' "$t"
    status=1
  fi
done
if ((status != 0)); then
  echo "Verification FAILED: the container serves an older mapping (or the table is empty in Postgres). Re-run without --check to restart." >&2
fi
exit $status
