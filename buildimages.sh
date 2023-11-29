#!/bin/bash
#

updateall="n"

while getopts c:l:a flag
do
    case "${flag}" in
        c) crunchbase=${OPTARG};;
        l) baselogo=${OPTARG};;
        a) updateall="y"
    esac
done

IFS=$'\n'
items=( $(yq '.landscape[] | select(.name != "LF Energy Member") | .subcategories[].items[] | select(.crunchbase == "*/'${crunchbase}'*") .name' landscape.yml) )

for item in "${!items[@]}"
do
  echo -n "Getting logo for ${items[$item]}..."
  if [ "$updateall" = "n" ] && [ -f "hosted_logos/${items[$item]}.svg" ] 
  then
    echo "SKIP - FILE EXISTS - hosted_logos/${items[$item]}.svg"
  elif ! [ -z "$baselogo" ]
  then
    eval echo $(curl --no-progress-meter -X POST -H "Content-Type: application/json" -d "{\"url\": \"${baselogo}\", \"caption\": \"${items[$item]}\", \"title\": \"\", \"captionWidth\": \"80\"}" https://autocrop.cncf.io/autocrop | jq ".result") > "hosted_logos/${items[$item]}.svg"
    echo "DONE"
  else
    echo "<svg><text>${items[$item]}</text></svg>" > text.svg
    if ! command -v inkscape &> /dev/null
    then
        echo "SKIP - INKSCAPE NOT FOUND"
    else
        inkscape text.svg --export-text-to-path --export-plain-svg --export-filename=${items[$item]} --export-area-drawing
        echo "DONE - TEXT LOGO"
    fi
  fi
done
