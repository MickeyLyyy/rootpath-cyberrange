# RootPath — Cyber Range (CTFd)

Plataforma de entrenamiento en ciberseguridad sobre **CTFd**, con:
- **Retos challenge-as-code** (18 retos: Web, Linux, AD, Blue, Crypto, Forensics) con narrativa dominicana.
- **Instancias efímeras por usuario**: cada alumno despliega su propio contenedor en un puerto propio.
- **Flag dinámica por usuario** (no se puede compartir la flag).
- **Dashboard propio** (desafíos, rutas, modo examen, analíticas, auditoría) y **landing de login/registro**.
- **Panel administrativo** RootPath.
- **VPN** (Tailscale y/o WireGuard) restringida a solo RootPath.
- **Pipeline generador** de retos (`challenges-v2/`).

## Componentes

| Ruta | Descripción |
|---|---|
| `plugins/rootpath/` | Plugin CTFd: API, modelos, plantillas (dashboard, welcome, admin), tipo de flag dinámica. |
| `challenges-v2/` | Pipeline generador de retos (specs + plantillas + orquestador). Genera `build/` (no versionado). |
| `agents/` | `lab_service.py` (deploy/destroy de instancias), `monitor.py`, `reaper.sh`. |
| `pipeline/`, `scripts/`, `expansion/` | Fases previas del proyecto. |
| `docs/` | Documentación por fases. |
| `docker-compose.yml` | CTFd + MariaDB + Redis. |

## Arquitectura (resumen)

```
Usuario ──(HTTPS/SSH)──> LXC "rootpath" (172.170.10.11)
   │                         ├─ CTFd (8000)
   │                         ├─ Instancias por usuario (puertos 30000-40000)
   └──(VPN Tailscale)──> Proxmox host (subnet route 172.170.10.11/32)
```

- Al pulsar **Abrir**, `lab_service` ejecuta `docker run` de una instancia del reto para ese usuario
  (`rp-<reto>-u<user_id>`), en un puerto libre, inyectando `RP_FLAG`.
- El **reaper** destruye las instancias al expirar el TTL; al **acertar la flag** se destruye al instante.
- CTFd valida con el tipo de flag `rootpath` (HMAC por usuario+reto).

## Puesta en marcha (resumen)

1. `docker compose up -d` (CTFd + DB + Redis).
2. Copiar `plugins/rootpath` dentro del contenedor CTFd (ya montado por `docker-compose.yml`).
3. Secretos (NO versionados): `.env`, `.admin_token`, `runtime/agent_key`, `runtime/flag_secret`, `agents/pve_token`.
4. Generar retos: `cd challenges-v2 && python3 run.py generate`.
5. Cargar a CTFd: `python3 run.py load`.
6. `lab_service` + `reaper` como servicios systemd.

## Seguridad

- **Nunca** subir a git: `.env`, `.admin_token`, `.student_token`, `agents/pve_token`, `runtime/agent_key`, `runtime/flag_secret`.
- Las instancias de reto son entornos aislados con límites de memoria/CPU; sin montajes del host.
- La VPN solo da acceso al contenedor RootPath (`172.170.10.11`).

## Licencia

Uso educativo. Los retos propios son de este proyecto; las apps/plantillas de terceros conservan su licencia.
