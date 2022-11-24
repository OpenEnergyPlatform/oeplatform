#!/bin/bash
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

echo "Starting apache2"

/usr/sbin/apache2ctl -DFOREGROUND
