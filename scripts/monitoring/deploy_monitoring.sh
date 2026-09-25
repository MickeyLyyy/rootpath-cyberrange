#!/bin/bash
set -e
D=/opt/rootpath/monitoring
mkdir -p "$D"
tar -xf /tmp/monitoring.tar -C /opt/rootpath
cd "$D"

DBPASS=$(docker exec rootpath-platform-db-1 printenv MYSQL_ROOT_PASSWORD)
GFPASS=$(head -c 18 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 16)
cat > .env <<EOF
DB_PASSWORD=$DBPASS
GF_PASSWORD=$GFPASS
EOF
chmod 600 .env

echo "=== docker compose up ==="
docker compose up -d --build
echo "=== esperando arranque ==="
sleep 30
docker compose ps

echo "=== salud ==="
curl -s -o /dev/null -w "grafana   = %{http_code}\n" http://127.0.0.1:3001/login
curl -s -o /dev/null -w "prometheus= %{http_code}\n" http://127.0.0.1:9090/-/ready
curl -s -o /dev/null -w "portainer = %{http_code}\n" -k https://127.0.0.1:9443/
echo "=== exporter (metricas) ==="
docker exec rp-mon-prometheus wget -qO- http://rootpath_exporter:9200/metrics 2>/dev/null | head -25 || echo "(exporter sin respuesta aun)"
echo "=== targets de prometheus ==="
curl -s http://127.0.0.1:9090/api/v1/targets 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);[print("  ",t["labels"].get("job"),t["health"],t.get("lastError","")) for t in d["data"]["activeTargets"]]' 2>/dev/null || echo "(prometheus sin respuesta)"

echo "$GFPASS" > /opt/rootpath/runtime/mon_gf_password
echo
echo "GRAFANA  -> http://172.170.10.11:3001   admin / $GFPASS"
echo "PORTAINER-> https://172.170.10.11:9443  (crear admin en el primer acceso)"
echo "PROMETHEUS-> http://172.170.10.11:9090"
