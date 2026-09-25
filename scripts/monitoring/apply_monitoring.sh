#!/bin/bash
set -e
D=/opt/rootpath/monitoring
cd "$D"

# .env: anadir Telegram si falta
if [ ! -f .env ]; then
  DBPASS=$(docker exec rootpath-platform-db-1 printenv MYSQL_ROOT_PASSWORD)
  GFPASS=$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 16)
  printf 'DB_PASSWORD=%s\nGF_PASSWORD=%s\n' "$DBPASS" "$GFPASS" > .env
fi
grep -q '^TELEGRAM_TOKEN=' .env || echo 'TELEGRAM_TOKEN=' >> .env
grep -q '^TELEGRAM_CHAT=' .env || echo 'TELEGRAM_CHAT=' >> .env
chmod 600 .env

# fijar token (si se pasa)
if [ -n "$1" ]; then
  sed -i "s|^TELEGRAM_TOKEN=.*|TELEGRAM_TOKEN=$1|" .env
fi

chmod +x render_alertmanager.sh
bash render_alertmanager.sh

echo "=== compose up ==="
docker compose up -d --build
sleep 20

echo "=== estado ==="
docker compose ps --format '{{.Name}} {{.State}} {{.Status}}'
echo "=== alertmanager config ==="
docker exec rp-mon-alertmanager amtool check-config /etc/alertmanager/alertmanager.yml 2>&1 | tail -3
echo "=== alertmanager health ==="
curl -s -o /dev/null -w "alertmanager=%{http_code}\n" http://127.0.0.1:9093/-/healthy
echo "=== reglas cargadas en prometheus ==="
curl -s http://127.0.0.1:9090/api/v1/rules 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);[print("  ",g["name"],"->",len(g["rules"]),"reglas") for g in d["data"]["groups"]]' 2>/dev/null
echo "=== alertmanagers conocidos por prometheus ==="
curl -s http://127.0.0.1:9090/api/v1/alertmanagers 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print("  activos:",[a["url"] for a in d["data"]["activeAlertmanagers"]])' 2>/dev/null
