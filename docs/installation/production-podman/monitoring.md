<!--
SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Monitoring

!!! info "You are here"

    Optional page of the **Production deployment (Podman)** guide, after
    **[Maintenance](maintenance.md)**. It adds monitoring beside a running
    installation without changing the app's containers.

The monitoring answers five questions:

| Question                                           | Source                                                                            |
| -------------------------------------------------- | --------------------------------------------------------------------------------- |
| Is each service up, and how fast does it answer?   | `oep-mon-blackbox` probes the app containers                                      |
| Is the host healthy (CPU, memory, load, disk)?     | `oep-mon-node` (node exporter)                                                    |
| Is each container healthy (CPU, memory, restarts)? | `oep-mon-podman` (podman exporter)                                                |
| Is the database healthy (connections, size)?       | `oep-mon-postgres` (postgres exporter)                                            |
| How is the platform used?                          | `oep-mon-usage.timer`, counts from the access log                                 |
| Is someone attacking it?                           | the same timers: failed logins, rejected requests, attack paths; four alert rules |

Prometheus (`oep-mon-prometheus`) stores the figures for 30 days, Grafana
(`oep-mon-grafana`) shows them in the dashboard **OEP / OEP overview**. Every
container joins the `oep` network and finds the others by name. Prometheus and
Grafana listen on `127.0.0.1` only; nothing else publishes a port.

## Install

Run as the service user, from the repository checkout the app was installed
from:

```sh
bash podman/monitoring/install.sh
```

It copies the units into place, renders the probe configuration with `OEP_URL`
from `~/.config/oeplatform/oep.env` (the app refuses requests for any other host
name) and creates `~/.config/oeplatform/monitoring.env`. Fill in both values
there, then create the read-only database role with the same password as
`DATA_SOURCE_PASS`:

```sh
podman exec -it postgres psql -U <POSTGRES_USER> -d postgres \
  -c "CREATE ROLE oep_monitoring LOGIN PASSWORD '<DATA_SOURCE_PASS>'; GRANT pg_monitor TO oep_monitoring;"
```

Start everything:

```sh
systemctl --user start oep-mon-prometheus oep-mon-grafana oep-mon-blackbox \
  oep-mon-node oep-mon-podman oep-mon-postgres
systemctl --user enable --now oep-mon-usage.timer oep-mon-usage-minute.timer
```

The container units start again after a reboot by themselves (as the app's do,
with linger enabled). `oep-mon-podman` starts the user's `podman.socket`.

## Look at it

From your own machine, tunnel the two ports:

```sh
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 <service-user>@<server>
```

Then open `http://localhost:3000` (user `admin`, password from
`monitoring.env`). Prometheus' **Status → Targets** page on
`http://localhost:9090` shows whether every source is reachable.

The first number of each `-L` is the port on your machine. If something there
already uses 3000 or 9090, pick any free one, e.g. `-L 13000:127.0.0.1:3000` and
then `http://localhost:13000`.

## Usage figures and privacy

Every hour, `podman/monitoring/usage/oep-usage.sh` reads the last 24 hours of
the app's access log from the journal and writes **counts only**: requests by
status class, API requests, successful logins, CSV and datapackage downloads,
and page views per area. No address, user name or query string is stored. The
monitoring's own probes (`?probe=blackbox`) and crawlers (a user agent
containing bot, crawl or spider) are left out; crawlers are counted on their
own. A second timer counts the requests of the last minute, every minute, for
the dashboard's **Requests per minute**. Once a day the hourly run also appends
the day before to `~/.local/state/oep-monitoring/usage.csv`, which keeps the
figures beyond Prometheus' 30 days.

Check the counting rules against the sample log:

```sh
podman/monitoring/usage/oep-usage.sh count < podman/monitoring/usage/testdata/access.log \
  | diff - podman/monitoring/usage/testdata/expected.prom
```

## Security figures and alerts

The same script counts, every minute and for the last 24 hours:

- **failed logins**: `POST /accounts/login/` answered 200 (the form shown
  again);
- **rejected requests**: answers 401 and 403;
- **requests to attack paths**: `.env`, `.git`, `.aws`, `wp-admin`, `wp-login`,
  `wp-content`, `phpmyadmin`, `cgi-bin`, `xmlrpc.php`, `actuator`, which this
  platform does not serve and scanners try everywhere.

Unlike the usage figures these include crawlers, because attacks often call
themselves bots.

Prometheus evaluates four alert rules from
`podman/monitoring/prometheus/rules.yml`: `ServiceDown` (a probe failing for 2
minutes), `DiskFillingUp` (over 85 % for 10 minutes), `FailedLoginWave` (over 10
failed logins per minute for 2 minutes) and `ScannerWave` (over 30 requests to
attack paths per minute for 2 minutes). The thresholds are starting values.
Firing alerts show on Prometheus' **Alerts** page and in the dashboard's
**Security** row; nothing sends them anywhere yet. After changing a rule, run
its test:

```sh
cd podman/monitoring/prometheus
podman run --rm -v "$PWD:/t:ro" -w /t --entrypoint promtool \
  docker.io/prom/prometheus:v3.15.0 test rules rules.test.yml
```

## Add a source

Add a container that serves metrics on the `oep` network and a job under
`scrape_configs` in `podman/monitoring/prometheus/prometheus.yml`, then
`systemctl --user restart oep-mon-prometheus`. To probe another service, add its
address to one of the `probe_*` jobs.

## Troubleshooting

| Symptom                               | Likely cause                                                                                                             |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| App probes fail, other probes succeed | `OEP_URL` differs from the host names the app accepts; re-run `install.sh`                                               |
| `postgres` target down                | role `oep_monitoring` missing, or its password differs from `DATA_SOURCE_PASS`                                           |
| `podman` target down                  | `systemctl --user status podman.socket`                                                                                  |
| Usage panels empty                    | `systemctl --user status oep-mon-usage`; the journal must hold the app's log: `journalctl --user -u oep-oeplatform -n 5` |
| Disk panel empty                      | the node exporter cannot read the host's mounts rootless; check `podman logs oep-mon-node`                               |
