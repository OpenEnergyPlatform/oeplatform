#!/bin/bash
# start-fuseki.sh

# Path to your Fuseki directory
FUSEKI_HOME="$HOME/oep-infrastructure/apache-jena-fuseki-4.9.0"

cd $FUSEKI_HOME

# Start the Fuseki server with a configuration file
./fuseki-server
