#!/usr/bin/env bash

python3 - "$FILE" <<'PY'
import sys
sys.path.insert(0, "/opt/rootpath/expansion")
from crypto_helpers import nt_hash
words = ["password","backup2023","Summer2023!","P@ssw0rd","rootpath2024","Winter2024!","svcpass"]
for line in open(sys.argv[1]):
    if ":" not in line: continue
    user, hb = line.strip().split(":", 1)
    for w in words:
        if nt_hash(w).hex() == hb:
            print("RP{%s_%s}" % (user, w)); sys.exit(0)
PY
