#!/bin/bash
cd /opt/rootpath/monitoring
echo "=== contenedores ==="
docker compose ps --format '{{.Name}} {{.State}} {{.Status}}'
echo
echo "=== salud ==="
curl -s -o /dev/null -w "grafana    = %{http_code}\n" http://127.0.0.1:3001/login
curl -s -o /dev/null -w "prometheus = %{http_code}\n" http://127.0.0.1:9090/-/ready
curl -s -o /dev/null -w "portainer  = %{http_code}\n" -k https://127.0.0.1:9443/
echo
echo "=== exporter metrics ==="
docker exec rp-mon-prometheus wget -qO- http://rootpath_exporter:9200/metrics 2>/dev/null | grep -vE '^#' | head -30 || echo "(sin respuesta)"
echo
echo "=== targets prometheus ==="
curl -s http://127.0.0.1:9090/api/v1/targets 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);[print("  ",t["labels"].get("job"),t["health"],t.get("lastError","")) for t in d["data"]["activeTargets"]]' 2>/dev/null
echo
echo "=== datasources grafana ==="
curl -s -u admin:"$(grep GF_PASSWORD /opt/rootpath/monitoring/.env | cut -d= -f2)" http://127.0.0.1:3001/api/datasources 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);[print("  ",x["name"],x["type"],x["url"]) for x in d] if isinstance(d,list) else print(d)' 2>/dev/null
echo "=== dashboards grafana ==="
curl -s -u admin:"$(grep GF_PASSWORD /opt/rootpath/monitoring/.env | cut -d= -f2)" "http://127.0.0.1:3001/api/search?query=RootPath" 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);[print("  ",x.get("title"),x.get("url")) for x in d] if isinstance(d,list) else print(d)' 2>/dev/null
echo
echo "=== credenciales ==="
echo "GF admin password: $(grep GF_PASSWORD /opt/rootpath/monitoring/.env | cut -d= -f2)"
