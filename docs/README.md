# RootPath - Fase 0 (Base)

Plataforma de labs/retos por certificacion. Esta fase despliega el panel **CTFd**
y **10 retos** (7 en Docker + 3 adjuntos estaticos) sobre el nodo Proxmox.

## Accesos
- Panel CTFd:        http://172.170.10.11:8000/
- Retos web:         http://172.170.10.11:8081 ... :8085
- Retos Linux (SSH): ssh player@172.170.10.11 -p 2201  y  -p 2202  (password: player)
- Admin CTFd:        ver CREDENCIALES.md

## Hosting
Todo vive en el contenedor LXC **112 "rootpath"** (Debian 12, 4 vCPU / 8 GB / 40 GB),
en el bridge vmbr0 (red de produccion 172.170.10.0/24).

## Estructura (dentro del LXC, /opt/rootpath)
- docker-compose.yml         -> CTFd + MariaDB + Redis
- .env                       -> secretos (chmod 600)
- .admin_token               -> token API admin (chmod 600)
- scripts/                   -> bootstrap_admin.py, load_challenges.py
- challenges/                -> challenge-as-code (7 retos Docker + 3 estaticos)
- docs/                      -> esta documentacion

## Estado
Fase 0 completa: un usuario completa un reto de extremo a extremo (verificado).
Sin Kali web (omitido por decision). Sin aislamiento por usuario (eso es Fase 1).
