#!/bin/bash
set -e
WORK=/opt/rootpath/forensic-build
rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"

FLAG='RP{analista_p3rd1d0_dns_7z_st3g0}'
XORKEY='analista'
P7Z='T3mp0r4l_2026!'
STEP='n0ch3_s1n_lun4'

echo "=== 1) pcap (hostname + exfil DNS + distractor) ==="
python3 - "$XORKEY" "$P7Z" <<'PY'
import sys, base64
from scapy.all import Ether, IP, UDP, TCP, DNS, DNSQR, DNSRR, Raw, wrpcap
key = sys.argv[1].encode(); p7z = sys.argv[2]
msg = ("user=analista;pass=" + p7z).encode()
enc = bytes(b ^ key[i % len(key)] for i, b in enumerate(msg))
b32 = base64.b32encode(enc).decode().rstrip("=")
chunks = [b32[i:i+12] for i in range(0, len(b32), 12)]
victim, dns = "192.168.50.23", "8.8.8.8"
pkts = []
pkts.append(Ether()/IP(src=victim, dst="192.168.50.1")/UDP(sport=44001, dport=53)/DNS(rd=1, qd=DNSQR(qname="analista.corp.local")))
pkts.append(Ether()/IP(src="192.168.50.1", dst=victim)/UDP(sport=53, dport=44001)/DNS(id=0, qr=1, qd=DNSQR(qname="analista.corp.local"), an=DNSRR(rrname="analista.corp.local", rdata="192.168.50.23")))
pkts.append(Ether()/IP(src=victim, dst="203.0.113.10")/TCP(sport=51000, dport=80, flags="PA")/Raw(load=b"GET /noticias HTTP/1.1\r\nHost: noticias.do\r\nUser-Agent: curl/8.5\r\n\r\n"))
pkts.append(Ether()/IP(src="203.0.113.10", dst=victim)/TCP(sport=80, dport=51000, flags="PA")/Raw(load=b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><!-- nota interna: RP{f4ls4_p1st4_n0_v4l3} --></html>"))
for i, c in enumerate(chunks):
    pkts.append(Ether()/IP(src=victim, dst=dns)/UDP(sport=53000+i, dport=53)/DNS(rd=1, qd=DNSQR(qname="%02d.%s.c2.darknet.do" % (i, c))))
wrpcap("captura.pcap", pkts)
print("pcap OK  chunks=%d" % len(chunks))
PY

echo "=== 2) foto + estego + 7z cifrado ==="
convert -size 1100x760 plasma:fractal foto.jpg
printf '%s' "$FLAG" > flag.txt
steghide embed -cf foto.jpg -ef flag.txt -p "$STEP" -f >/dev/null 2>&1
python3 - "$STEP" <<'PY'
import sys, base64
s = sys.argv[1]
open("nota.txt", "w").write("clave para la imagen (INVERTIDA, luego base64 -> decode, luego invertir):\n" + base64.b64encode(s[::-1].encode()).decode() + "\n")
PY
7z a -p"$P7Z" -mhe=on secretos.7z nota.txt foto.jpg >/dev/null
echo "7z OK"

echo "=== 3) rootfs del disco ==="
mkdir -p rootfs/home/analista rootfs/srv/backups rootfs/etc
cp secretos.7z rootfs/srv/backups/secretos.7z
printf 'root:x:0:0:root:/root:/bin/bash\nanalista:x:1000:1000:Analista:/home/analista:/bin/bash\n' > rootfs/etc/passwd
printf 'cmV2aXNhIGVsIHRyYWZpY28gRE5TLCBsYSBsbGF2ZSBlcyBlbCBub21icmUgZGVsIGVxdWlwbw==\n' > rootfs/home/analista/fake.txt
cat > rootfs/home/analista/.bash_history <<'HIST'
ls -la
cd /srv/backups
7z a -mhe=on secretos.7z nota.txt foto.jpg
history -c
HIST

echo "=== 4) imagen ext4 + borrado recuperable ==="
truncate -s 64M disco.img
mke2fs -t ext4 -d rootfs -F disco.img >/dev/null 2>&1
debugfs -w -R "rm /home/analista/.bash_history" disco.img >/dev/null 2>&1 || true
echo "disco OK"

echo "=== 5) empaquetar evidencia.zip ==="
rm -f evidencia.zip
7z a -tzip evidencia.zip captura.pcap disco.img >/dev/null
ls -la evidencia.zip captura.pcap disco.img
echo "=== FIN ==="

