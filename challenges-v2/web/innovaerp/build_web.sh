#!/bin/bash
set -e
D=/opt/rootpath/challenges-v2/build/innovaerp-panel
rm -rf "$D"; mkdir -p "$D"
cp -r /tmp/webapp_extreme/. "$D"/
mkdir -p "$D/static"
echo "=== descargar Bootstrap (plantilla real, MIT) ==="
curl -fsSL -o "$D/static/bootstrap.min.css" https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css
curl -fsSL -o "$D/static/bootstrap.bundle.min.js" https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js
ls -l "$D/static/"
echo "=== build imagen ==="
docker build -t rootpath-v2-innovaerp-panel "$D" 2>&1 | tail -4
echo "=== lab_map ==="
python3 /tmp/upd_labmap.py
