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
items=( $(ls -ag hosted_logos | grep "9406 Apr 11 16:48") )

for item in "${!items[@]}"
do
  replacetext="-rw-r--r--@    1 staff      9406 Apr 11 16:48 " 
  logofile=${items[$item]}
  logofile=${logofile/$replacetext/}
  replacetext='.svg'
  logoname=${logofile/$replacetext/}
  logofile="hosted_logos/$logofile"
  echo -n "Making logo for $logoname..."
  echo "<svg><text>$logoname</text></svg>" > text.svg
  inkscape text.svg --export-text-to-path --export-plain-svg --export-filename=$logofile --export-area-drawing
  echo "DONE"
done
