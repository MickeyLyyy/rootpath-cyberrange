#!/bin/bash
set -e
D=/opt/rootpath/monitoring
set -a; . "$D/.env"; set +a
CHAT="${TELEGRAM_CHAT:-0}"
sed -e "s|__TELEGRAM_TOKEN__|${TELEGRAM_TOKEN}|g" \
    -e "s|__TELEGRAM_CHAT__|${CHAT}|g" \
    "$D/alertmanager/alertmanager.yml.tmpl" > "$D/alertmanager/alertmanager.yml"
chmod 600 "$D/alertmanager/alertmanager.yml"
echo "alertmanager.yml renderizado (chat_id=$CHAT)"
