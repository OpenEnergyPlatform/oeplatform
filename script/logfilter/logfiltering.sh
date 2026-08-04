#!/usr/bin/env bash

# SPDX-FileCopyrightText: 2026 Ariyosena Sutandang  <https://github.com/AriyosenaS> © Reiner Lemoine Institut
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# Exit if no container name is provided
if [ -z "$1" ]; then
    echo "Error: No Docker container provided."
    echo "Usage: ./logfiltering.sh <container_name_or_id> [time_window]"
    echo "Example: ./logfiltering.sh web_app 1h    (Analyzes last 1 hour)"
    echo "Example: ./logfiltering.sh web_app 30m   (Analyzes last 30 minutes)"
    exit 1
fi

CONTAINER_NAME="$1"
# Default to 24 hours if a second argument isn't provided
TIME_WINDOW="${2:-24h}" 

# Ensure the docker command is found when running from cron
export PATH=$PATH:/usr/local/bin:/usr/bin:/bin

# Create a secure temporary file to store the logs
LOG_FILE=$(mktemp)

# Ensure the temp file is deleted when the script exits, even if it crashes
trap "rm -f $LOG_FILE" EXIT

# Fetch logs from docker
# Note: Redirecting both stdout and stderr (2>&1) just in case web logs go to stderr
docker logs --since "$TIME_WINDOW" "$CONTAINER_NAME" > "$LOG_FILE" 2>&1

# Check if the docker command failed or if the file is empty
if [ ! -s "$LOG_FILE" ]; then
    echo "No logs found for container '$CONTAINER_NAME' in the last $TIME_WINDOW or container doesn't exist."
    exit 0
fi

echo "Server Log Insights"
echo "======================================================"
echo "Analyzing container : $CONTAINER_NAME"
echo "Time window         : Last $TIME_WINDOW"
echo "------------------------------------------------------"

# --- 1. Overall Traffic & Health ---
TOTAL_REQS=$(wc -l < "$LOG_FILE" | tr -d ' ')
echo "Total Requests Processed    : $TOTAL_REQS"

echo "HTTP Status Codes:"
# Extract column 6 (Status Code), count unique occurrences, and sort them
awk '{print $6}' "$LOG_FILE" | sort | uniq -c | sort -nr | while read count status; do
    echo " $status : $count requests"
done

echo ""
# --- 2. User Actions ---
LOGIN_SUBMISSIONS=$(grep -c "POST /accounts/login/ HTTP" "$LOG_FILE")
DB_DASHBOARD_HITS=$(grep -c "\"GET /database/ HTTP" "$LOG_FILE")
METADATA_VIEWS=$(grep -c "GET /database/metadata-viewer/" "$LOG_FILE")
echo " Login Form Submissions      : $LOGIN_SUBMISSIONS"
echo " Database Dashboard Visits   : $DB_DASHBOARD_HITS"
echo " Metadata/Details Views       : $METADATA_VIEWS"

# --- 3. Dynamic Tag Filters ---
EXTRACTED_TAGS=$(grep "tags=" "$LOG_FILE" | awk -F'tags=' '{print $2}' | awk -F'[ &"]' '{print $1}' | sort -u)

if [ ! -z "$EXTRACTED_TAGS" ]; then
    for TAG_NAME in $EXTRACTED_TAGS; do
        TAG_HITS=$(grep -c "tags=${TAG_NAME}" "$LOG_FILE")
        echo " '${TAG_NAME}' Tag Filters       : $TAG_HITS"
    done
fi

# --- 4. Download Tracking ---
echo ""
echo "Data Exports Initiated:"
CSV_DOWNLOADS=$(grep -c "form=csv" "$LOG_FILE")
DATAPACKAGE_DOWNLOADS=$(grep -c "form=datapackage" "$LOG_FILE")
echo "    CSV Files                : $CSV_DOWNLOADS"
echo "    Datapackages (ZIP)       : $DATAPACKAGE_DOWNLOADS"

# Extract exact table names that were downloaded
echo "   Detailed Downloads:"
grep "/rows/?form=" "$LOG_FILE" | awk '{print $4}' | while read url; do
    # Break down the URL: /api/v0/tables/biomass_capacities/rows/?form=csv
    TABLE_NAME=$(echo "$url" | awk -F'/' '{print $5}')
    FILE_TYPE=$(echo "$url" | awk -F'form=' '{print $2}')
    echo "      - $TABLE_NAME (Format: $FILE_TYPE)"
done

# --- 5. Performance / Heavy Requests ---
echo ""
echo " Top 3 Heavy File Transfers (Bandwidth):"
# Sort numerically (reverse) by column 7 (bytes), take the top 3, format into KB
sort -k7 -nr "$LOG_FILE" | head -n 3 | awk '{
    size=$7/1024; 
    printf " %.1f KB -> %s\n", size, $4
}'

echo "======================================================"
