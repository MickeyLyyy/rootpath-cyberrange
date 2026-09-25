#!/bin/bash
KEY=$(cat /opt/rootpath/runtime/agent_key)
echo "=== deploy maquina uid991 ==="
curl -s -H "X-Agent-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"name":"Colmado - Panel de Diagnostico","uid":991,"host_port":34002,"flag":"RP{t}"}' \
  http://127.0.0.1:9001/lab/deploy >/dev/null
echo "=== deploy web uid992 ==="
curl -s -H "X-Agent-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"name":"ArcadeScore - Tabla de Puntuaciones","uid":992,"host_port":34003,"flag":"RP{t}"}' \
  http://127.0.0.1:9001/lab/deploy >/dev/null
sleep 7
echo "=== labels target maquina ==="
docker inspect rp-colmado-u991 --format '{{json .Config.Labels}}'
echo "=== labels atacante maquina ==="
docker inspect rp-colmado-atk-u991 --format '{{json .Config.Labels}}'
echo "=== labels web ==="
docker inspect rp-arcadescore-u992 --format '{{json .Config.Labels}}'
echo "=== bot /contenedores ==="
docker exec rp-mon-bot python3 -c "import bot; print(bot.answer('/contenedores'))"
echo "=== cleanup ==="
curl -s -H "X-Agent-Key: $KEY" -H 'Content-Type: application/json' -d '{"name":"Colmado - Panel de Diagnostico","uid":991,"container":"rp-colmado-u991"}' http://127.0.0.1:9001/lab/destroy >/dev/null
curl -s -H "X-Agent-Key: $KEY" -H 'Content-Type: application/json' -d '{"name":"ArcadeScore - Tabla de Puntuaciones","uid":992,"container":"rp-arcadescore-u992"}' http://127.0.0.1:9001/lab/destroy >/dev/null
echo done
