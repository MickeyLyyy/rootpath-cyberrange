#!/bin/bash
set -e
BASE=/opt/rootpath/challenges-v2/build
build_one() {
  local svc=$1 src=$2
  local d=$BASE/$svc
  rm -rf "$d"; mkdir -p "$d"
  cp -r "$src"/. "$d"/
  curl -fsSL https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css \
    -o "$d/static/bootstrap.min.css"
  docker build -q -t rootpath-v2-$svc "$d" >/dev/null
  echo "built rootpath-v2-$svc"
}
build_one arcadescore /tmp/arcade
build_one skinshop /tmp/skins
build_one savequest /tmp/save
build_one craftworld /tmp/craft
echo "BUILD EASY COMPLETO"
