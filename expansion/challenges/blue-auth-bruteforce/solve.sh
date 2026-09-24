#!/usr/bin/env bash

python3 - "$FILE" <<'PY'
import sys, re, base64
for line in open(sys.argv[1]):
    for m in re.finditer(r"echo ([A-Za-z0-9+/=]+) >", line):
        print(base64.b64decode(m.group(1)).decode())
PY
