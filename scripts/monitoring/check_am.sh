#!/bin/bash
sleep 5
echo "=== estado ==="
docker ps --filter name=rp-mon- --format '{{.Names}} {{.Status}}'
echo "=== amtool check-config ==="
docker exec rp-mon-alertmanager amtool check-config /etc/alertmanager/alertmanager.yml 2>&1 | tail -3
echo "=== alertmanager health ==="
curl -s -o /dev/null -w "alertmanager=%{http_code}\n" http://127.0.0.1:9093/-/healthy
echo "=== reglas en prometheus ==="
curl -s http://127.0.0.1:9090/api/v1/rules 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);[print("  ",g["name"],"->",len(g["rules"]),"reglas") for g in d["data"]["groups"]]' 2>/dev/null
echo "=== alertmanagers activos en prometheus ==="
curl -s http://127.0.0.1:9090/api/v1/alertmanagers 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print("  ",[a["url"] for a in d["data"]["activeAlertmanagers"]])' 2>/dev/null
