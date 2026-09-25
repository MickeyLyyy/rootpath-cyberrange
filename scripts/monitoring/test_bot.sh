#!/bin/bash
echo "=== estado contenedor ==="
docker ps --filter name=rp-mon-bot --format '{{.Names}} {{.Status}}'
echo "=== logs ==="
docker logs rp-mon-bot --tail 5 2>&1
echo
for c in /estado /contenedores /retos /instancias /usuarios /host /acciones; do
  echo "----- $c -----"
  docker exec rp-mon-bot python3 -c "import bot; print(bot.answer('$c'))" 2>&1
done
echo "----- frase natural: 'cuantos contenedores hay' -----"
docker exec rp-mon-bot python3 -c "import bot; print(bot.answer('cuantos contenedores hay'))" 2>&1
