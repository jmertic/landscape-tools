#!/bin/bash
#
# Script to create project/product logos for when an organization doesn't have a logo for the
# given project/product. Creates so they are all uniform in size and dimension
#
# Copyright this project and it's contributors
# SPDX-License-Identifier: Apache-2.0
#

# company logo to use
logo='ibm.svg'
# array of project/product names
products=('crc32-s390x' 'IBM Z Workload Scheduler' 'Db2 DevOps Experience for z/OS' 'Service Automation Suite' 'Service Management Suite for z/OS' 'Service Management Unite' 'IBM® Z Netview' 'libica' 'qclib' 's390-tools' 'Shared Memory Communication Tools' 'snIPL' 'source VIPA' 'System Loader (sysload)' 'z/OS Connect EE' 'z/OS Node Accessor' 'z/OS Tools' 'zfcp HBA API library' 'Remote System Explorer API' 'Zowe CLI CICS Deploy')
# sed replace to make the logo higher
sedreplacelogheight='s/viewBox="0 0 400 245"/viewBox="0 0 400 300"/g'
# y coordinate for text to start
textheighty='240'

## CHANGE NOTHING BELOW HERE ##
for i in ${!products[@]};
do
  product=${products[$i]}
  filename="$(tr [A-Z] [a-z] <<< "$product")"
  filename="${filename// /-}"
  filename="${filename//\//}"
  filename="${filename//®/}"
  filename="${filename//(/}"
  filename="${filename//)/}"
  filename="${filename//™/}.svg"
  texttoadd="<text x=\"50%\" y=\"${textheighty}\" style=\"font: 22px sans-serif;alignment-baseline: middle; text-anchor:middle;\">${product}</text></svg>"
  echo "Creating ${filename} for ${product}"
  cp $logo $filename
  sed -i'.original' "${sedreplacelogheight}" $filename
  sed -i'.original' "s|</svg>|${texttoadd}|g" $filename
  inkscape $filename --export-text-to-path --export-plain-svg --export-filename=$filename
done
