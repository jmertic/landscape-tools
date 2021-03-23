#!/bin/bash
#
# Download the latest crunchbase organization data
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#

wget -qO- https://api.crunchbase.com/bulk/v4/bulk_export.tar.gz\?user_key\=$CRUNCHBASE_KEY_4 | tar xvz - organizations.csv
