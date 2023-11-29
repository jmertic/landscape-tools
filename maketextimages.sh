#!/bin/bash
#

newonly="n"

while getopts c:l:n flag
do
    case "${flag}" in
        c) crunchbase=${OPTARG};;
        n) newonly="y"
    esac
done

IFS=$'\n'
items=( $(yq '.landscape[] | select(.name != "LF Energy Member") | .subcategories[].items[] | select(.crunchbase == "*/'${crunchbase}'*") .name' landscape.yml) )
IFS=$'\n'

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
  echo "<svg><text>$logoname</text></svg>" > text.svg
  inkscape text.svg --export-text-to-path --export-plain-svg --export-filename=$logofile --export-area-drawing
  echo "DONE"
done
