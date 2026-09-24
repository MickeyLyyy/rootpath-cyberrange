# Seguridad

## Secretos (nunca en git)
| Archivo | Contenido |
|---|---|
| `/opt/rootpath/.env` | password de DB, `SECRET_KEY`, admin password. |
| `/opt/rootpath/.admin_token` | token API admin CTFd. |
| `/opt/rootpath/.student_token` | token API de usuario (pruebas). |
| `/opt/rootpath/agents/pve_token` | token API Proxmox (monitor). |
| `/opt/rootpath/runtime/agent_key` | clave plugin ↔ lab_service. |
| `/opt/rootpath/runtime/flag_secret` | secreto de las flags dinámicas. |

`.gitignore` los excluye y en el repo se **puró** `.student_token` del historial.
Aun así, si algún token pudo exponerse, **rótalo** (regenerar en CTFd/Proxmox).

## Aislamiento de las instancias de reto
Cada instancia es un contenedor (`rp-<reto>-u<uid>`) creado con:
- `--memory 256m --cpus 0.5` (límites de recursos),
- **sin** montajes del host ni del socket docker,
- en un puerto propio (30000-40000), uno por usuario,
- `--restart=no` (no se re-levantan solas).

Los retos son **intencionadamente vulnerables**: el usuario puede obtener root **dentro** de su
contenedor. Riesgos y mitigaciones:
- **Escape de contenedor**: usar imágenes mínimas, evitar `--privileged`/capabilities extra,
  y (recomendado) un **host/LXC dedicado** o user-namespaces.
- **Pivoting**: red docker dedicada sin acceso a la red de CTFd/DB. Considerar `--network` aislada
  e incluso bloquear salida a Internet de las instancias si no se necesita.

## Auditoría
Toda acción sobre instancias se registra en `rp_lab_actions`: `user_id` único, `user_name`, `ip`,
acción, reto, servicio y resultado. Vista **solo admin** en el panel (los usuarios no la ven).

## Control de acceso a los retos
- Solo usuarios autenticados despliegan; **rate-limit** (30/min) y **máximo 3 instancias** por usuario.
- **Flag única por usuario** (no se puede compartir): `RP{<reto>_<hmac>}`.
- El acertar la flag destruye **tu** instancia al instante.

## VPN
Solo da acceso a **`172.170.10.11`** (RootPath), no al host Proxmox ni al resto de la LAN.
Detalle en [VPN.md](VPN.md).

## Endurecimiento pendiente / recomendado
- Correr las instancias en un **LXC/host separado** de CTFd.
- `--cap-drop=ALL` + `--security-opt no-new-privileges` (si el reto lo permite).
- Rotar periódicamente: `agent_key`, `flag_secret`, tokens de API y claves de VPN.
- Limitar por firewall los puertos de instancia a la interfaz VPN.
- Backups cifrados de la base de datos.

## Superficie expuesta
| Servicio | Puerto | Exposición |
|---|---|---|
| CTFd | 8000 | LXC (LAN; VPN para externos). |
| lab_service | 9001 | Solo localhost/LAN + `X-Agent-Key`. |
| Instancias | 30000-40000 | LXC (LAN; VPN para externos). |
| Proxmox | 8006/22 | Host (no expuesto a la VPN). |
