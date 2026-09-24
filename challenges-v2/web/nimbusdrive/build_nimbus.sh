#!/bin/bash
set -e
D=/opt/rootpath/challenges-v2/build/nimbusdrive
rm -rf "$D"; mkdir -p "$D"
cp -r /tmp/nimbus/. "$D"/
mkdir -p "$D/static"
curl -fsSL -o "$D/static/bootstrap.min.css" https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css
docker build -t rootpath-v2-nimbusdrive "$D" 2>&1 | tail -3
python3 /tmp/upd_labmap_nimbus.py
