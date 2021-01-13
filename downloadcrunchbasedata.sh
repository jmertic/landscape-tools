#!/bin/bash
#
# Download the latest crunchbase organization data
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#

wget -qO- https://api.crunchbase.com/bulk/v4/bulk_export.tar.gz\?user_key\=92985d13ba92a637d51538e9420b67fe | tar xvz - organizations.csv
