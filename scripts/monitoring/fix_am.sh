#!/bin/bash
set -e
cd /opt/rootpath/monitoring
sed -i 's|^TELEGRAM_CHAT=.*|TELEGRAM_CHAT=1|' .env
bash render_alertmanager.sh
docker compose up -d alertmanager >/dev/null 2>&1
sleep 10
echo "=== estado ==="
docker ps --filter name=rp-mon-alertmanager --format '{{.Names}} {{.Status}}'
echo "=== amtool ==="
docker exec rp-mon-alertmanager amtool check-config /etc/alertmanager/alertmanager.yml 2>&1 | tail -2
echo "=== health ==="
curl -s -o /dev/null -w "alertmanager=%{http_code}\n" http://127.0.0.1:9093/-/healthy
echo "=== alertmanagers en prometheus ==="
curl -s http://127.0.0.1:9090/api/v1/alertmanagers 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print("  activos:",[a["url"] for a in d["data"]["activeAlertmanagers"]])' 2>/dev/null
