#!/bin/bash
# SOLVE del reto forense extremo (valida la cadena completa)
set -e
W=/opt/rootpath/forensic-build
cd "$W"

echo "=== 0) extraer evidencia ==="
rm -rf solve; mkdir solve; cd solve
7z x -y ../evidencia.zip >/dev/null

echo "=== 1) pcap: hostname ==="
HOST=$(python3 - <<'PY'
from scapy.all import rdpcap, DNSQR
for p in rdpcap("captura.pcap"):
    if p.haslayer(DNSQR):
        q = p[DNSQR].qname.decode(errors="ignore").rstrip(".")
        if q.endswith("corp.local"):
            print(q.split(".")[0]); break
PY
)
echo "hostname: $HOST"

echo "=== 2) reensamblar exfil DNS + base32 + XOR ==="
PW=$(python3 - "$HOST" <<'PY'
import sys, base64
from scapy.all import rdpcap, DNSQR
key = sys.argv[1].encode()
parts = {}
for p in rdpcap("captura.pcap"):
    if p.haslayer(DNSQR):
        q = p[DNSQR].qname.decode(errors="ignore").strip(".")
        if q.endswith(".c2.darknet.do"):
            seq, chunk = q.split(".")[0], q.split(".")[1]
            parts[int(seq)] = chunk
b32 = "".join(parts[k] for k in sorted(parts))
b32 += "=" * ((8 - len(b32) % 8) % 8)
enc = base64.b32decode(b32)
msg = bytes(b ^ key[i % len(key)] for i, b in enumerate(enc)).decode()
print(msg.split("pass=")[1])
PY
)
echo "password 7z: $PW"

echo "=== 3) extraer secretos.7z del disco (debugfs) ==="
debugfs -R "dump /srv/backups/secretos.7z secretos.7z" disco.img >/dev/null 2>&1
7z x -y -p"$PW" secretos.7z >/dev/null
echo "en 7z:"; ls -1

echo "=== 4) passphrase de la imagen (base64 + invertir) ==="
STEP=$(python3 - <<'PY'
import base64
line = [l for l in open("nota.txt") if l.strip() and "base64" not in l][0].strip()
print(base64.b64decode(line).decode()[::-1])
PY
)
echo "steghide pass: $STEP"

echo "=== 5) estego -> flag ==="
steghide extract -sf foto.jpg -p "$STEP" -xf flag_out.txt -f >/dev/null 2>&1
echo "FLAG: $(cat flag_out.txt)"

echo "=== extra: archivo borrado (carving con strings) ==="
strings disco.img | grep -A1 "history" | head -6
