<!--
SPDX-FileCopyrightText: 2026 Ariyosena Sutandang <https://github.com/AriyosenaS> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
-->

A Bash script using `awk` to extract HTTP access metrics from Django application containers (supporting both **Podman** and **Docker**). It parses access logs via regex matching to ignore startup output and stack traces, appending time-series data to a structured **CSV** file.

---

## Output

Results are appended to a cumulative CSV file located by default at:
`media/log_metrics/metrics_<container_name>.csv`

### Captured Fields
- `timestamp`, `container`, `window`
- Status codes: `status_200`, `status_3xx`, `status_4xx`, `status_5xx`
- Total requests and application views (`logins`, `dashboard_hits`, `metadata_views`)
- Download tracking (`csv_downloads`, `datapackage_downloads`, `table_downloads`)
- Exact tag query counts (`tag_counts`)
- Bandwidth bottlenecks: Top 3 heaviest transfers (`1_heavy_download`, `2_heavy_download`, `3_heavy_download`)

---

## Arguments

```bash
./logfiltering.sh <container_name> [time_window] [output_csv]