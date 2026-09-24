#!/usr/bin/env bash

python3 - "$FILE" <<'PY'
import sys, re, base64
labels = []
for line in open(sys.argv[1]):
    m = re.search(r"	([a-z2-7]+)\.exfil\.rootpath\.local", line)
    if m: labels.append(m.group(1))
data = "".join(labels).upper()
pad = "=" * ((8 - len(data) % 8) % 8)
try:
    print(base64.b32decode(data + pad).decode())
except Exception:
    print(base64.b32decode(data).decode())
PY
