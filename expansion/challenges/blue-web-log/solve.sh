#!/usr/bin/env bash

python3 - "$FILE" <<'PY'
import sys, re, base64
for m in re.finditer(r"data=([A-Za-z0-9+/=]+)", open(sys.argv[1]).read()):
    try:
        d = base64.b64decode(m.group(1)).decode()
        if "RP{" in d: print(d)
    except Exception: pass
PY
