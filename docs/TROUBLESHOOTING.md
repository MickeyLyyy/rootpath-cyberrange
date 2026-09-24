# Troubleshooting

## CTFd / plugin

**`500 Internal Server Error` en un reto Web con `NameError: name 'flag' is not defined`.**
Las apps web deben usar el marcador `{{RP_FLAG}}` (no una variable Python `flag`). Regenerar y
rebuild de imágenes tras corregir la plantilla.

**`/api/agent/map` devuelve 404 (HTML).**
La ruta correcta es `/plugins/rootpath/api/agent/map` (blueprint con prefijo `/plugins/rootpath`).

**Las páginas antiguas de CTFd (p. ej. `/cyber-range`) siguen mostrándose.**
`_hide_ctfd` intercepta las rutas de **páginas CTFd** y redirige al dashboard; si añades páginas
nuevas, se cubren automáticamente (se consulta `Pages.query`).

**El usuario admin aparece como “Estudiante” y no ve “Auditoría”.**
`/api/v1/users/me` **no** devuelve `type`. El dashboard usa `/plugins/rootpath/api/me`
(que expone `admin`). Recargar con Ctrl+Shift+R.

**`SAWarning: incompatible polymorphic identity 'rootpath'`.**
Aviso benigno: CTFd define `Flags` con `polymorphic_on=type` sin subclases. La validación funciona.

## Instancias de laboratorio

**El botón Abrir no levanta nada.**
- Revisar `runtime/lab_map.json` (el reto debe tener entrada con `image`/`internal_port`).
- `systemctl status rootpath-lab` y `journalctl -u rootpath-lab`.
- Que exista la imagen: `docker images | grep rootpath-v2-<slug>`.

**Los contenedores se quedan abiertos.**
- Cierran por **TTL** (reaper, `lab_ttl_minutes`, por defecto 60) o al **acertar la flag**.
- Verifica el timer: `systemctl list-timers rootpath-reaper.timer`.
- Si una instancia quedó huérfana: `docker rm -f $(docker ps -aq --filter name=rp-)`.

**“No se pudo desplegar el laboratorio”.**
- Puerto ocupado o fuera de rango; el plugin asigna 30000-40000 y evita duplicados en `rp_lab_instances`.
- Ver detalle en `rp_lab_actions.detail`.

**La IP en auditoría es `172.170.10.10` (host) en vez de la del cliente.**
Hay SNAT en medio. En Tailscale, usa `--snat-subnet-routes=false` + ruta `100.64.0.0/10` en el LXC.

## VPN Tailscale

**Los clientes no entran ni hacen ping a `172.170.10.11`.**
1. **El cliente no acepta rutas**: activar “Use Tailscale subnets” / `tailscale up --accept-routes`.
2. **El host ve 0 peers** (netmap obsoleto): guardar/editar la ACL fuerza un netmap nuevo; o
   `systemctl restart tailscaled`.
3. **Tailnets distintos**: el host y los clientes deben estar en el **mismo** tailnet
   (comprobar `tailscale status` en el cliente: debe aparecer `rootpath-gw`).
4. **Ruta no aprobada**: aprobar `172.170.10.11/32` en la consola.
5. **Ruta de retorno**: que el LXC tenga `100.64.0.0/10 via 172.170.10.10`.

**Compilar/instalar: el repo `mega.nz` rompe `apt-get update`.**
Desactivar ese repo (comentar su línea) o tolerar el error; el resto de repos funcionan.

## Red / Docker

**`docker compose` no encuentra los servicios.**
El compose de retos usa `name: rootpath-v2`; pasar el `-f` correcto
(`challenges-v2/build/docker-compose.yml`).

**Persistencia:** el LXC es un contenedor Proxmox; los datos de CTFd están en volúmenes docker
(`ctfd-db`, `ctfd-uploads`, `ctfd-cache`). No los borres.

## Git

**Se subió un secreto.** Rotarlo y purgarlo del historial:
```bash
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch <archivo>' --prune-empty -- --all
rm -rf .git/refs/original; git reflog expire --expire=now --all; git gc --prune=now
```
