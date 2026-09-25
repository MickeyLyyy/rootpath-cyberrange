#!/bin/bash
TOKEN=$(grep '^TELEGRAM_TOKEN=' /opt/rootpath/monitoring/.env | cut -d= -f2-)
UPD=$(curl -s "https://api.telegram.org/bot$TOKEN/getUpdates")
CHAT=$(echo "$UPD" | python3 -c 'import sys,json
d=json.load(sys.stdin); r=d.get("result",[])
print(r[-1]["message"]["chat"]["id"] if r and "message" in r[-1] else "")' 2>/dev/null)
if [ -z "$CHAT" ]; then
  echo "SIN MENSAJES: abre https://t.me/Root_Path_bot y pulsa /start primero."
  exit 1
fi
sed -i "s|^TELEGRAM_CHAT=.*|TELEGRAM_CHAT=$CHAT|" /opt/rootpath/monitoring/.env
bash /opt/rootpath/monitoring/render_alertmanager.sh
docker restart rp-mon-alertmanager >/dev/null
sleep 6
echo "chat_id=$CHAT configurado y alertmanager reiniciado"
curl -s -o /dev/null -w "test send = %{http_code}\n" -X POST \
  "https://api.telegram.org/bot$TOKEN/sendMessage" \
  --data-urlencode "chat_id=$CHAT" \
  --data-urlencode "text=RootPath: alertas de Telegram configuradas ✅"
