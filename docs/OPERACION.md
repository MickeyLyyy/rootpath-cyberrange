# Operación

## Tareas frecuentes

### Reiniciar servicios
```bash
docker compose -f /opt/rootpath/docker-compose.yml restart ctfd   # CTFd + plugin
systemctl restart rootpath-lab                                     # lab_service
systemctl restart rootpath-reaper.timer                            # reaper
```

### Ver instancias activas (contenedores por usuario)
```bash
docker ps --filter "name=rp-"                    # instancias vivas
docker ps -a --filter "name=rp-"                 # todas
docker rm -f $(docker ps -aq --filter "name=rp-")  # limpiar todas (CUIDADO)
```

### Ver/limpiar la tabla de instancias y auditoría
```bash
DB="docker exec rootpath-platform-db-1 mariadb -uctfd -p$DB_PASS ctfd"
$DB -e "select id,user_id,challenge_name,host_port,expires_at from rp_lab_instances;"
$DB -e "select id,user_name,ip,action,challenge_name,result,created_at from rp_lab_actions order by id desc limit 20;"
$DB -e "delete from rp_lab_instances;"           # solo si hay desajustes
```
(`DB_PASS` está en `.env` como `DB_PASSWORD`.)

### Cambiar el TTL de las instancias
```bash
echo 30 > /opt/rootpath/runtime/lab_ttl_minutes   # minutos (por defecto 60)
```

### Limitar instancias simultáneas por usuario
Editar `LAB_MAX_PER_USER` en `plugins/rootpath/api.py` (por defecto 3) y reiniciar CTFd.

### Rango de puertos de instancias
`LAB_PORT_MIN`/`LAB_PORT_MAX` (30000-40000) en `plugins/rootpath/api.py`.

## Gestión de retos
```bash
cd /opt/rootpath/challenges-v2
python3 run.py generate          # (re)genera build/ con flags nuevas
python3 run.py load              # publica/actualiza en CTFd (idempotente)
```
- Para **añadir un reto**: editar `specs.py` + una plantilla `tpl_*.py`, `generate`, build, `load`.
- Para **cambiar puertos/TTL/plantilla**: editar y regenerar/rebuild.

## Auditoría
- Panel: dashboard → **Auditoría** (solo admin) → tabla con usuario, id, IP, acción, servicio, resultado.
- Resultados: `ok`, `ok:auto_ttl` (reaper), `ok:auto_solve` (al acertar), `error:*`, `denied:*`.

## Backups
- Backups de archivos editados: `/opt/rootpath/.backup-*` (creados en cada despliegue).
- Base de datos CTFd: volumen docker `ctfd-db`. Ejemplo:
```bash
docker exec rootpath-platform-db-1 sh -c 'mysqldump -uctfd -p$MYSQL_PASSWORD ctfd' > /root/ctfd_$(date +%F).sql
```

## Logs
```bash
docker logs --tail 100 rootpath-platform-ctfd-1
journalctl -u rootpath-lab -n 50
journalctl -u rootpath-reaper -n 20
journalctl -u tailscaled -n 30        # si usas Tailscale
```

## Healthchecks
```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/login      # 200
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9001/lab/status # 403 (sin key)
```

## Git
```bash
cd /opt/rootpath
git add -A && git commit -m "..." && git push
```
Repo privado: `github.com/MickeyLyyy/rootpath-cyberrange`.
