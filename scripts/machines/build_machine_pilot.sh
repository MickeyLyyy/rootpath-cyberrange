#!/bin/bash
set -e
BASE=/opt/rootpath/challenges-v2/build
d=$BASE/colmado; rm -rf "$d"; mkdir -p "$d"; cp -r /tmp/colmado/. "$d"/
docker build -q -t rootpath-v2-colmado "$d" >/dev/null && echo "built rootpath-v2-colmado"
d=$BASE/attacker; rm -rf "$d"; mkdir -p "$d"; cp -r /tmp/attacker/. "$d"/
docker build -q -t rootpath-attacker "$d" >/dev/null && echo "built rootpath-attacker"
docker images | grep -E 'rootpath-v2-colmado|rootpath-attacker'
