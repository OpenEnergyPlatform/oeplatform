#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
# SPDX-FileCopyrightText: 2026 Ariyosena Sutandang <https://github.com/AriyosenaS> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Usage figures from the app's access log. Only counts leave this script: no
# address, no user name, no query string. Run hourly by oep-mon-usage.timer:
#   - textfile/oep_usage.prom: the last 24 hours, read by the node exporter;
#   - usage.csv: one block per day, appended once for yesterday. Prometheus
#     keeps 30 days; this is the record kept beyond that.
# `oep-usage.sh count < access.log` prints the figures of a log on stdin.

set -euo pipefail

STATE="$HOME/.local/state/oep-monitoring"

count() {
    # POSIX awk only, so it runs under mawk (Debian's default) as well as gawk.
    awk '
    # %h %l %u %t "%r" %>s %b "%{User-Agent}i" %D   (podman/apache2.conf);
    # lines in plain Common Log Format count too, with no user agent.
    $6 ~ /^"[A-Z]+$/ && $9 ~ /^[0-9][0-9][0-9]$/ {
        method = substr($6, 2); path = $7; status = $9
        ua = ""
        if (match($0, /" [0-9][0-9][0-9] ([0-9]+|-) "/)) {
            ua = substr($0, RSTART + RLENGTH); sub(/" [0-9]+$/, "", ua)
        }
        if (path ~ /[?&]probe=blackbox/ || ua ~ /Blackbox Exporter/) next
        if (tolower(ua) ~ /bot|crawl|spider/) { bots++; next }

        requests[substr(status, 1, 1) "xx"]++
        base = path; sub(/\?.*/, "", base)
        if (base ~ /^\/api\//) api++
        if (method == "POST" && base ~ /^\/accounts\/login\/?$/ && status == 302) logins++
        if (status !~ /^2/) next
        if (match(path, /[?&]form=(csv|datapackage)($|&)/)) downloads[path ~ /form=csv/ ? "csv" : "datapackage"]++
        if (method == "GET" && base !~ /^\/(api|static|media|captcha)\//) {
            split(base, seg, "/"); area = seg[2] == "" ? "home" : seg[2]
            if (area !~ /^(home|database|factsheets|scenario-bundles|ontology|viewer|oekg|user|accounts)$/) area = "other"
            pageviews[area]++
        }
    }
    END {
        # A fixed list, so every series exists from the first run on.
        split("2xx 3xx 4xx 5xx", c, " "); for (i = 1; i <= 4; i++) printf "oep_usage_requests{class=\"%s\"} %d\n", c[i], requests[c[i]]
        printf "oep_usage_bot_requests %d\noep_usage_api_requests %d\noep_usage_logins %d\n", bots, api, logins
        printf "oep_usage_downloads{format=\"csv\"} %d\noep_usage_downloads{format=\"datapackage\"} %d\n", downloads["csv"], downloads["datapackage"]
        n = split("home database factsheets scenario-bundles ontology viewer oekg user accounts other", a, " ")
        for (i = 1; i <= n; i++) printf "oep_usage_pageviews{area=\"%s\"} %d\n", a[i], pageviews[a[i]]
    }'
}

# The app container's stdout, which the Quadlet unit hands to the journal.
journal() { journalctl --user -u oep-oeplatform -o cat --since "$1" ${2:+--until "$2"}; }

if [ "${1:-}" = count ]; then count; exit; fi

mkdir -p "$STATE/textfile"
journal -24h | count > "$STATE/textfile/oep_usage.prom.tmp"
# Renamed into place, so the node exporter never reads half a file.
mv "$STATE/textfile/oep_usage.prom.tmp" "$STATE/textfile/oep_usage.prom"

day=$(date -d yesterday +%F)
csv="$STATE/usage.csv"
[ -f "$csv" ] || echo "date,metric,value" > "$csv"
if ! grep -q "^$day," "$csv"; then
    journal yesterday today | count \
        | awk -v d="$day" '{ m = $1; gsub(/\{[a-z]+="/, ":", m); gsub(/"\}/, "", m); print d "," m "," $2 }' >> "$csv"
fi
