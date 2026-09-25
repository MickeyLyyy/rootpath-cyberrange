#!/bin/bash
KEY=$(cat /opt/rootpath/runtime/agent_key)
systemctl restart rootpath-lab; sleep 2
run() {
  local name="$1" uid="$2" port="$3" container="$4" flag="$5" solver="$6"
  echo "=== deploy: $name ==="
  RESP=$(curl -s -H "X-Agent-Key: $KEY" -H 'Content-Type: application/json' \
    -d "{\"name\":\"$name\",\"uid\":$uid,\"host_port\":$port,\"flag\":\"$flag\"}" \
    http://127.0.0.1:9001/lab/deploy)
  echo "$RESP"
  sleep 6
  echo "=== SOLVE ==="
  python3 /tmp/$solver $port
  echo "=== destroy ==="
  curl -s -H "X-Agent-Key: $KEY" -H 'Content-Type: application/json' \
    -d "{\"name\":\"$name\",\"uid\":$uid,\"container\":\"$container\"}" \
    http://127.0.0.1:9001/lab/destroy; echo
}
run "ArcadeScore - Tabla de Puntuaciones" 996 31011 rp-arcadescore-u996 "RP{arcade_test_local}" solve_arcade.py
run "SkinShop - Tienda de Skins" 995 31012 rp-skinshop-u995 "RP{skins_test_local}" solve_skins.py
run "SaveQuest - Visor de Partidas" 994 31013 rp-savequest-u994 "RP{save_test_local}" solve_save.py
run "CraftWorld - Panel del Servidor" 993 31014 rp-craftworld-u993 "RP{craft_test_local}" solve_craft.py
echo "TEST EASY COMPLETO"
