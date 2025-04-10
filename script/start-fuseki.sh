#!/bin/bash

# SPDX-FileCopyrightText: 2025 Bryan Lancien <bryanlancien.ui@gmail.com>
# SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
#
# SPDX-License-Identifier: MIT

# start-fuseki.sh

# Path to your Fuseki directory
FUSEKI_HOME="$HOME/oep-infrastructure/apache-jena-fuseki-4.9.0"

cd $FUSEKI_HOME

# Start the Fuseki server with a configuration file
./fuseki-server
