#!/usr/bin/env bash

python3 - "$FILE" <<'PY'
import sys, json, base64
d = json.load(open(sys.argv[1]))
for e in d.get("edges", []):
    if e.get("label") == "AdminTo" and "DOMAIN CONTROLLERS" in e.get("target",""):
        for u in d["users"]:
            if u["name"] == e["source"]:
                print(base64.b64decode(u["properties"]["description"]).decode())
PY
