#!/bin/bash
set -e
R="10.100.0.0/14"
# 1) raw PREROUTING: permitir acceso externo a los rangos (por delante del anti-spoof de Docker)
for S in 100.64.0.0/10 172.170.10.10; do
  iptables -t raw -C PREROUTING -s "$S" -d "$R" -j ACCEPT 2>/dev/null || \
    iptables -t raw -I PREROUTING 1 -s "$S" -d "$R" -j ACCEPT
done
# 2) DOCKER-USER: permitir el forward hacia los rangos
iptables -w -C DOCKER-USER -i eth0 -d "$R" -j ACCEPT 2>/dev/null || \
  iptables -w -I DOCKER-USER 1 -i eth0 -d "$R" -j ACCEPT

echo "--- raw PREROUTING ---"; iptables -t raw -S PREROUTING | head -4
echo "--- DOCKER-USER ---"; iptables -S DOCKER-USER

# 3) persistencia
cat > /etc/systemd/system/rootpath-expose.service <<'UNIT'
[Unit]
Description=RootPath: exponer rangos internos (raw + docker forward)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/sh -c '\
  for S in 100.64.0.0/10 172.170.10.10; do \
    iptables -t raw -C PREROUTING -s $S -d 10.100.0.0/14 -j ACCEPT 2>/dev/null || \
    iptables -t raw -I PREROUTING 1 -s $S -d 10.100.0.0/14 -j ACCEPT; \
  done; \
  iptables -w -C DOCKER-USER -i eth0 -d 10.100.0.0/14 -j ACCEPT 2>/dev/null || \
  iptables -w -I DOCKER-USER 1 -i eth0 -d 10.100.0.0/14 -j ACCEPT'

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now rootpath-expose.service >/dev/null 2>&1
echo "expose persistido"
