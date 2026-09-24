# Arquitectura

## Topología

```
                         (Internet) 74.244.193.132
                                │
                     Router MikroTik (172.170.10.1)
                                │  vmbr0 · 172.170.10.0/24
                                │
              ┌─────────────────┴─────────────────────────┐
              │            Proxmox host (172.170.10.10)    │
              │  · WireGuard  wg0 10.13.13.0/24 (UDP 51820)│
              │  · Tailscale  rootpath-gw (subnet route)   │
              │  · firewall: solo reenvía a .11            │
              │                                            │
              │   LXC 112 "rootpath" (172.170.10.11)       │
              │   ├─ CTFd        :8000   (docker)          │
              │   ├─ MariaDB / Redis (docker)              │
              │   ├─ lab_service :9001   (systemd)         │
              │   ├─ reaper      (systemd timer)           │
              │   └─ Instancias de reto  :30000-40000      │
              │        (docker: rp-<reto>-u<user>)         │
              └────────────────────────────────────────────┘
```

## Componentes

| Componente | Ubicación | Rol |
|---|---|---|
| **CTFd** | docker `rootpath-platform-ctfd-1` | Motor de retos, usuarios, flags, scoreboard. |
| **MariaDB / Redis** | docker | Base de datos y caché de CTFd. |
| **Plugin RootPath** | `/opt/rootpath/plugins/rootpath` (montado en CTFd) | API, modelos, dashboard, panel admin, landing, flag dinámica. |
| **lab_service** | `/opt/rootpath/agents/lab_service.py` · systemd `rootpath-lab` (:9001) | `deploy`/`destroy` de contenedores por usuario. |
| **reaper** | `/opt/rootpath/agents/reaper.sh` · systemd `rootpath-reaper.timer` | Destruye instancias expiradas cada 30 s. |
| **monitor** | `agents/monitor.py` · `rootpath-monitor` | Vigilancia de métricas del nodo (Fase 3). |
| **Pipeline de retos** | `/opt/rootpath/challenges-v2/` | Genera/valida/carga retos (challenge-as-code). |
| **Imágenes de reto** | docker `rootpath-v2-<slug>` | Base de las instancias efímeras. |

## Flujos

### A) Login / navegación de usuario
1. `GET /` → 302 a `/plugins/rootpath/welcome` (o al dashboard si hay sesión).
2. Landing (welcome.html) → login/registro reales de CTFd (POST `/login`, `/register` con `nonce`).
3. Autenticado → `/plugins/rootpath/dashboard` (SPA con Desafíos, Rutas, Examen, Analíticas, Writeups, Usuarios, y **Auditoría/Panel Admin** si es admin).

### B) Desplegar una instancia de reto (por usuario)
1. Usuario pulsa **Abrir** en la tarjeta *Entorno*.
2. `POST /plugins/rootpath/api/lab/control {action:"start"}`.
3. El plugin:
   - verifica rate-limit y límite por usuario (3),
   - asigna un **puerto libre** (30000-40000),
   - calcula la **flag del usuario** (`flags.user_flag`),
   - llama al lab_service `POST /lab/deploy {name,uid,host_port,flag}`.
4. lab_service: `docker run -d --name rp-<reto>-u<uid> -p <port>:<internal> -e RP_FLAG=<flag> <imagen>`.
5. El plugin guarda la instancia en `rp_lab_instances` con `expires_at` (TTL) y registra auditoría.

### C) Resolver y autocierre
1. Usuario envía la flag → `POST /api/v1/challenges/attempt`.
2. CTFd valida con el tipo de flag **`rootpath`** (recalcula la flag del usuario).
3. Si acierta, un hook `after_request` del plugin destruye **su** instancia (`ok:auto_solve`).

### D) TTL / reaper
1. `rootpath-reaper.timer` (~30 s) llama `GET /api/agent/reap` con `X-Agent-Key`.
2. El endpoint destruye las instancias con `expires_at <= now` (`ok:auto_ttl`).

### E) Acceso remoto (VPN)
- **Tailscale**: nodo `rootpath-gw` anuncia `172.170.10.11/32`; los miembros del tailnet aceptan rutas y llegan al contenedor.
- **WireGuard**: clientes en `10.13.13.0/24`; el host reenvía **solo** a `172.170.10.11`.
