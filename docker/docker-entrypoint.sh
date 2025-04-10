#!/bin/bash

# SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
# SPDX-FileCopyrightText: 2025 Eike Broda <git@ebroda.de>
# SPDX-FileCopyrightText: 2025 Johann Wagner <johann@wagnerdevelopment.de>
# SPDX-FileCopyrightText: 2025 Jonas Huber <38939526+jh-RLI@users.noreply.github.com>
#
# SPDX-License-Identifier: MIT

set -euo pipefail

sleep 5

echo "Checking for Configuration"

FILE=/app/oeplatform/securitysettings.py
FILE_DEFAULT=/app/oeplatform/securitysettings.py.default
if [ -f $FILE ]; then
   echo "File $FILE exists, we do not copy the default configuration."
else
   echo "File $FILE does not exist, copying default configuration."
   cp $FILE_DEFAULT $FILE
fi

echo "Migrating Databases..."
echo "Migrating Django database..."
python manage.py migrate
echo "Migrating local database..."
python manage.py alembic upgrade head

echo "Compress stylesheets & JavaScript"
python manage.py compress

echo "Starting apache2"

/usr/sbin/apache2ctl -DFOREGROUND
