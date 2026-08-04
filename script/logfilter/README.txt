SPDX-FileCopyrightText: 2026 Ariyosena Sutandang  <https://github.com/AriyosenaS> © Reiner Lemoine Institut

SPDX-License-Identifier: AGPL-3.0-or-later

A Bash script using grep and awk to filter docker logs

## Manual Usage
Run the script directly from the terminal to print insights to your console.
Syntax:  ./logfiltering.sh <container_name> <time_window>
Example: ./logfiltering.sh oeplatform-web-dev 1h

## Automated Execution (Cronjob)
To run regularly, use `crontab -e`

Then, add a line at the bottom of the file specifying the schedule, absolute path to the script, container name, time window, and absolute path for the output file.

Example: Run every hour and save to the log_metrics directory
0 * * * * /path/to/your/project/script/logfilter/logfiltering.sh <container_name> 1h > /path/to/your/project/script/log_metrics/latest_report_$(date +\%H\%d\%m\%y).txt 2>&1

Example: Run every 2 hours and save to the log_metrics directory
0 */2 * * * /path/to/your/project/script/logfilter/logfiltering.sh <container_name> 2h > /path/to/your/project/script/log_metrics/latest_report_$(date +\%H\%d\%m\%y).txt 2>&1

## Arguments
1. Container Target : The name of the Docker container to inspect (e.g., oeplatform-web-dev). Do not use container IDs if they are subject to change.
2. Time Window      : The look-back period passed to Docker's --since flag.
                      Format: 5m (minutes), 1h (hours), 24h (days).
                      *Crucial: When automating, ensure this window matches your cron schedule so you do not double-count or miss logs.*

## Troubleshooting
- Cron executes in an empty environment. Always use absolute paths (e.g., /home/user/... instead of ~/...).
- The output destination directory must exist before the cronjob runs, otherwise the job will fail silently.
- In crontab, the `%` character in the date command must be escaped with a backslash (`\%`).
