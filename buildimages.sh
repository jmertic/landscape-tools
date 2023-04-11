#!/bin/bash
#

while getopts c:l: flag
do
    case "${flag}" in
        c) crunchbase=${OPTARG};;
        l) baselogo=${OPTARG};;
    esac
done

IFS=$'\n'
items=( $(yq '.landscape[] | select(.name != "LF Energy Member") | .subcategories[].items[] | select(.crunchbase == "*/'${crunchbase}'*") .name' landscape.yml) )

#items=("makani" "transitfeed" "Carbon free energy for Google Cloud regions" "Analysis-Ready, Cloud Optimized ERA5" "weather-tools")
#baselogo="https://landscape.lfenergy.org/logos/google-llc.svg"
for item in "${!items[@]}"
do
  echo -n "Getting logo for ${items[$item]}..."
  eval echo $(curl --no-progress-meter -X POST -H "Content-Type: application/json" -d "{\"url\": \"${baselogo}\", \"caption\": \"${items[$item]}\", \"title\": \"\", \"captionWidth\": \"80\"}" https://autocrop.cncf.io/autocrop | jq ".result") > "hosted_logos/${items[$item]}.svg"
  echo "DONE"
done
