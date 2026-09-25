# RootPath · Monitoring

Stack de observabilidad y gestión para el cyber range (solo LAN/Tailscale, nunca público).

## Servicios
| Servicio | URL | Uso |
|---|---|---|
| Portainer | https://172.170.10.11:9443 | gestión de contenedores (crear admin en el primer acceso) |
| Grafana | http://172.170.10.11:3001 | dashboards y alertas |
| Prometheus | http://172.170.10.11:9090 | motor de métricas |

Credenciales de Grafana: en `monitoring/.env` (`GF_PASSWORD`) — **no versionado**.

## Piezas
- `node_exporter` → host (Proxmox vía LXC).
- `cadvisor` → métricas por contenedor (`rp-*`, ctfd, db...).
- `rootpath_exporter` → métricas propias del range (instancias, deploys, puertos, solves, submissions).
- `prometheus` → almacenamiento (retención 30d).
- `grafana` → dashboards provisionados en la carpeta **RootPath**:
  - RootPath · Infra
  - RootPath · Laboratorios
  - RootPath · Plataforma

## Métricas propias (`rootpath_exporter`)
`rootpath_instances_active`, `rootpath_instances_by_kind`, `rootpath_ports_used`,
`rootpath_deploys_total{action,result}`, `rootpath_users_total`, `rootpath_solves_total`,
`rootpath_submissions_total{type}`, `rootpath_hint_unlocks_total`,
`rootpath_challenges_total{state}`, `rootpath_up`.

## Bot de Telegram (@Root_Path_bot)
Responde en lenguaje natural y con comandos sobre todos los servicios:
`/estado /contenedores /instancias /retos /usuarios /solves /puertos /host /acciones /ayuda`.
Fuentes: MariaDB (CTFd), Prometheus y la API de Docker. Solo responde a `ALLOWED_CHAT` (`TELEGRAM_CHAT`).

## Etiquetas de contenedores
Cada contenedor de laboratorio lleva:
`rootpath.challenge` (título del reto), `rootpath.service`, `rootpath.user`,
`rootpath.kind` (web|machine), `rootpath.role` (target|attacker).
Visibles en Portainer y en el bot (`/contenedores`).


## Operación
```bash
cd /opt/rootpath/monitoring
docker compose ps
docker compose up -d --build
docker compose logs -f rootpath_exporter
```

## Seguridad
- Solo accesible desde la LAN (172.170.10.0/24) / tailnet. Proteger Portainer con
  contraseña fuerte (es root-equivalente: monta el socket de Docker).
- `.env` contiene la clave de MariaDB y la de Grafana: permisos 600, fuera de git.
