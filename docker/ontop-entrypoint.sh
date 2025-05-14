#!/bin/sh

set -e

echo "📦 Preparing JDBC directory..."
mkdir -p /opt/ontop/jdbc

echo "📥 Downloading PostgreSQL JDBC driver..."
curl -L https://jdbc.postgresql.org/download/postgresql-42.7.3.jar -o /opt/ontop/jdbc/postgresql.jar

chmod +x /opt/ontop/jdbc/postgresql.jar

echo "📦 Copying config files..."
cp /source/* /opt/ontop/input/

echo "✅ Done."
