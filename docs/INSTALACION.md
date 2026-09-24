# Instalación

Todo vive en el **LXC 112 "rootpath"** (Debian 12, 4 vCPU / 8 GB / 40 GB) del host Proxmox.
Ruta base: `/opt/rootpath`. Docker + docker compose instalados.

## 1) Plataforma CTFd
```bash
cd /opt/rootpath
docker compose up -d          # ctfd (8000), db (mariadb 10.11), cache (redis)
```
`docker-compose.yml` monta el plugin y el runtime:
```yaml
volumes:
  - ./plugins/rootpath:/opt/CTFd/CTFd/plugins/rootpath
  - ./runtime:/opt/CTFd/runtime
```

Credenciales de admin: `/opt/rootpath/.env` (`ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`).

## 2) Plugin RootPath
El plugin ya está en `plugins/rootpath/` (montado). Al reiniciar CTFd se cargan modelos
(`rp_*`, creados con `db.create_all()`), el tipo de flag `rootpath`, las sobrescrituras de
`login.html`/`register.html` (landing) y el blueprint de la API.

```bash
docker compose -f /opt/rootpath/docker-compose.yml restart ctfd
```

## 3) Secretos (NO versionados)
| Archivo | Para qué |
|---|---|
| `.env` | credenciales CTFd/DB. |
| `.admin_token` | API token admin (usado por scripts). |
| `.student_token` | API token de un usuario normal (pruebas/agente). |
| `agents/pve_token` | token API Proxmox (monitor). |
| `runtime/agent_key` | clave compartida plugin ↔ lab_service/agente. |
| `runtime/flag_secret` | secreto para las flags dinámicas. |

Generar `flag_secret` si no existe:
```bash
head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n' > /opt/rootpath/runtime/flag_secret
```

## 4) Servicios systemd
```bash
# Control de laboratorios (deploy/destroy)
systemctl enable --now rootpath-lab.service

# Reaper (TTL)
systemctl enable --now rootpath-reaper.timer
```
- `rootpath-lab.service` → `/opt/rootpath/agents/lab_service.py` (puerto 9001, `X-Agent-Key`).
- `rootpath-reaper.{service,timer}` → `/opt/rootpath/agents/reaper.sh` (cada 30 s).

## 5) Retos (pipeline)
```bash
cd /opt/rootpath/challenges-v2
python3 run.py generate      # genera build/ (Dockerfiles, app.py, manifest)
docker compose -f build/docker-compose.yml build   # construye rootpath-v2-<slug>
python3 run.py validate      # opcional: solve.sh end-to-end
python3 run.py load          # crea retos+flags+hints en CTFd y mapea cert/dominio
```
Ver [RETOS_PIPELINE.md](RETOS_PIPELINE.md).

## 6) lab_map.json
`runtime/lab_map.json` mapea **título del reto → servicio/imagen/puerto/kind**:
```json
{
  "El Colmadón de la Duarte": {
    "service": "el-colmadon-de-la-duarte",
    "image": "rootpath-v2-el-colmadon-de-la-duarte",
    "internal_port": 5000, "kind": "web"
  }
}
```
Los retos de Linux añaden `ssh_user`/`ssh_pass`.

## 7) VPN (opcional)
Ver [VPN.md](VPN.md). Tailscale (subnet route) o WireGuard (UDP 51820 → host).

## Verificación rápida
```bash
docker ps                                   # ctfd/db/cache arriba
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/login
systemctl is-active rootpath-lab rootpath-reaper.timer
```
