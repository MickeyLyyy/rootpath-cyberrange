#!/usr/bin/env bash

python3 - "$FILE" <<'PY'
import sys, base64, re
s = open(sys.argv[1], errors="ignore").read()
for m in re.finditer(r"^description:: (.+)$", s, re.M):
    try:
        d = base64.b64decode(m.group(1)).decode(errors="ignore")
        if "RP{" in d: print(d.strip())
    except Exception: pass
PY
