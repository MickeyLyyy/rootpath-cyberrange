#!/bin/bash
set -e
# 1) Ruta del host Proxmox hacia los rangos de RootPath (viven dentro del LXC 112)
ip route replace 10.100.0.0/14 via 172.170.10.11
ip route | grep 10.100 || true

# 2) Persistencia de la ruta
cat > /etc/systemd/system/rootpath-range-route.service <<'UNIT'
[Unit]
Description=RootPath: ruta a los rangos internos (LXC 112)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/ip route replace 10.100.0.0/14 via 172.170.10.11
ExecStop=/sbin/ip route del 10.100.0.0/14 via 172.170.10.11

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now rootpath-range-route.service >/dev/null 2>&1
echo "ruta persistida"

# 3) Anunciar por Tailscale (union con la ruta ya aprobada)
tailscale up --hostname=rootpath-gw \
  --advertise-routes=172.170.10.11/32,10.100.0.0/14 \
  --accept-dns=false --snat-subnet-routes=false --accept-routes=false >/dev/null 2>&1
echo "rutas anunciadas"

echo "--- estado tailscale ---"
tailscale status --json > /tmp/ts2.json 2>/dev/null
python3 - <<'PY'
import json
s=json.load(open("/tmp/ts2.json"))["Self"]
print("advertised:", s.get("AdvertisedRoutes"), "| primary:", s.get("PrimaryRoutes"))
PY
