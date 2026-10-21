#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2026 Ariyosena Sutandang <https://github.com/AriyosenaS> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

if [ -z "$1" ]; then
    echo "Error: No container provided." >&2
    echo "Usage: ./logfiltering.sh <container_name_or_id> [time_window] [output_csv]" >&2
    exit 1
fi

CONTAINER_NAME="$1"
TIME_WINDOW="${2:-24h}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_CSV="${3:-${REPO_ROOT}/media/log_metrics/metrics_${CONTAINER_NAME}.csv}"

mkdir -p "$(dirname "$OUTPUT_CSV")"

export PATH=$PATH:/usr/local/bin:/usr/bin:/bin
export USER_ID=$(id -u)
export XDG_RUNTIME_DIR="/run/user/${USER_ID}"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"

if command -v podman >/dev/null 2>&1; then
    CONTAINER_CLI="podman"
elif command -v docker >/dev/null 2>&1; then
    CONTAINER_CLI="docker"
else
    echo "Error: Neither podman nor docker CLI found in PATH." >&2
    exit 1
fi

LOG_FILE=$(mktemp)
trap 'rm -f "$LOG_FILE"' EXIT

$CONTAINER_CLI logs --since "$TIME_WINDOW" "$CONTAINER_NAME" > "$LOG_FILE" 2>&1

if [ ! -s "$LOG_FILE" ]; then
    exit 0
fi

TIMESTAMP=$(date -Iseconds)

METRICS=$(awk '
BEGIN {
    total_reqs = 0
    s200 = 0
    s3xx = 0
    s4xx = 0
    s5xx = 0
    logins = 0
    dashboards = 0
    metadata = 0
    csv_dl = 0
    dp_dl = 0
    h1_b = 0; h1_u = ""
    h2_b = 0; h2_u = ""
    h3_b = 0; h3_u = ""
}
{
    if (match($0, /"(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH) ([^ "]+) HTTP\/[0-9.]+" ([0-9]{3}) ([0-9]+)/, m)) {
        method = m[1]
        url = m[2]
        status = m[3] + 0
        bytes = m[4] + 0

        total_reqs++

        if (status == 200) {
            s200++
        } else if (status >= 300 && status < 400) {
            s3xx++
        } else if (status >= 400 && status < 500) {
            s4xx++
        } else if (status >= 500 && status < 600) {
            s5xx++
        }

        if (method == "POST" && url ~ /^\/accounts\/login\/?/) {
            logins++
        }
        if (url ~ /^\/database\/?(\?.*)?$/) {
            dashboards++
        }
        if (url ~ /^\/database\/metadata-viewer\/?/) {
            metadata++
        }

        if (url ~ /form=csv([& "('\''\?]|$)/) {
            csv_dl++
        }
        if (url ~ /form=datapackage([& "('\''\?]|$)/) {
            dp_dl++
        }

        # Use distinct array t_arr for captures to avoid scalar conflicts
        scan_url = url
        while (match(scan_url, /tags=([^ &"'\''\?]+)/, t_arr)) {
            tags[t_arr[1]]++
            scan_url = substr(scan_url, RSTART + RLENGTH)
        }

        if (url ~ /\/rows\/\?.*form=/) {
            if (match(url, /\/api\/v0\/tables\/([^\/\?]+)\/rows\/\?.*form=([^ &"'\''\?]+)/, tbl)) {
                key = tbl[1] "(" tbl[2] ")"
                table_dls[key]++
            }
        }

        # Keep running top 3 largest transfers
        if (bytes > h1_b) {
            h3_b = h2_b; h3_u = h2_u
            h2_b = h1_b; h2_u = h1_u
            h1_b = bytes; h1_u = url
        } else if (bytes > h2_b) {
            h3_b = h2_b; h3_u = h2_u
            h2_b = bytes; h2_u = url
        } else if (bytes > h3_b) {
            h3_b = bytes; h3_u = url
        }
    }
}
END {
    if (total_reqs == 0) {
        exit 0
    }

    # Iterate using distinct scalar key names
    tag_str = ""
    for (tag_name in tags) {
        tag_str = (tag_str ? tag_str ";" : "") tag_name ":" tags[tag_name]
    }

    dl_str = ""
    for (tbl_name in table_dls) {
        dl_str = (dl_str ? dl_str ";" : "") tbl_name ":" table_dls[tbl_name]
    }

    h1 = (h1_b > 0) ? sprintf("%.1f:%s", h1_b / 1024, h1_u) : ""
    h2 = (h2_b > 0) ? sprintf("%.1f:%s", h2_b / 1024, h2_u) : ""
    h3 = (h3_b > 0) ? sprintf("%.1f:%s", h3_b / 1024, h3_u) : ""

    printf "%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n",
        total_reqs, s200, s3xx, s4xx, s5xx, logins, dashboards, metadata,
        csv_dl, dp_dl, tag_str, dl_str, h1, h2, h3
}' "$LOG_FILE")

if [ -z "$METRICS" ]; then
    exit 0
fi

IFS=$'\t' read -r TOTAL_REQS STATUS_200 STATUS_3XX STATUS_4XX STATUS_5XX \
    LOGIN_SUBMISSIONS DB_DASHBOARD_HITS METADATA_VIEWS \
    CSV_DOWNLOADS DATAPACKAGE_DOWNLOADS TAG_COUNTS DOWNLOADED_TABLES \
    HEAVY_1 HEAVY_2 HEAVY_3 <<< "$METRICS"

if [ ! -f "$OUTPUT_CSV" ]; then
    echo "timestamp,container,window,total_reqs,status_200,status_3xx,status_4xx,status_5xx,logins,dashboard_hits,metadata_views,csv_downloads,datapackage_downloads,tag_counts,table_downloads,1_heavy_download,2_heavy_download,3_heavy_download" > "$OUTPUT_CSV"
fi

echo "${TIMESTAMP},${CONTAINER_NAME},${TIME_WINDOW},${TOTAL_REQS},${STATUS_200},${STATUS_3XX},${STATUS_4XX},${STATUS_5XX},${LOGIN_SUBMISSIONS},${DB_DASHBOARD_HITS},${METADATA_VIEWS},${CSV_DOWNLOADS},${DATAPACKAGE_DOWNLOADS},\"${TAG_COUNTS}\",\"${DOWNLOADED_TABLES}\",\"${HEAVY_1}\",\"${HEAVY_2}\",\"${HEAVY_3}\"" >> "$OUTPUT_CSV"
