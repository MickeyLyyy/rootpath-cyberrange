#!/bin/bash
# RootPath - backup diario de la base CTFd y de la configuracion del plugin.
# Retencion: 14 dias. Instalado por /etc/cron.d/rootpath-backup.
set -e
DEST=/var/backups/rootpath
mkdir -p "$DEST"
TS=$(date +%Y%m%d-%H%M%S)
DB=$(docker ps -qf name=rootpath-platform-db | head -1)
if [ -n "$DB" ]; then
  docker exec "$DB" sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction ctfd' 2>/dev/null | gzip > "$DEST/ctfd-$TS.sql.gz"
fi
tar czf "$DEST/rootpath-config-$TS.tar.gz" -C /opt/rootpath \
    plugins runtime agents scripts 2>/dev/null || true
# retencion
find "$DEST" -type f -mtime +14 -delete
echo "$(date -u +%FT%TZ) backup ok -> $DEST (ts=$TS)"
