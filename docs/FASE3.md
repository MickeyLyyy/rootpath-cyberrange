# RootPath - Fase 3 (Agentes operativos)

Implementado con minimo privilegio: los agentes usan un **token de API de Proxmox**
restringido, una **allowlist** de acciones, **limites de frecuencia** y **auditoria
encadenada** (hash chain) inmutable.

## Proxmox: identidades de minimo privilegio
- Usuario: `rootpath-monitor@pve`
- Token: `rootpath-monitor@pve!monitor` (privsep=0)
- Pool gestionado: `agentmanaged`
- Roles y ACL:
  - `RootPathReadOnly` (Sys.Audit, Pool.Audit, VM.Audit) en `/` y `/nodes`  -> solo lectura
  - `RootPathMonitor`  (VM.Audit, VM.PowerMgmt, Pool.Audit) en `/pool/agentmanaged` -> SOLO puede
    apagar/queries de invitados de ese pool. No puede tocar el resto del nodo.
- El token NO puede: crear/borrar VMs, tocar red, cambiar config, acceder a almacenamiento.

## Agentes (en el LXC 112, /opt/rootpath/agents)
- `bus.py`   : bus de acciones con allowlist por agente + rate limit + auditoria.
- `actions.py`: implementacion de acciones (PVE API + CTFd API).
- `audit.py` : log append-only con encadenado SHA-256 (verificable).
- `monitor.py`: bucle de vigilancia (servicio systemd `rootpath-monitor`).
- `cli.py`   : invocacion manual y consulta de auditoria.

### Allowlists
- monitor: read_metrics, list_guests, pool_members, stop_guest, set_deploy_paused, write_status, alert
- curador: list_paths, recommend_next, request_deploy
- tutor  : get_hint
- read_flag NO esta permitido para ningun agente (existe para demostrar el bloqueo).

### Limites de frecuencia
monitor 120/min, curador 30/min, tutor 30/min.

## Umbrales del monitor
- CPU del nodo > 60% o RAM > 85%  =>  pausa despliegues + apaga el invitado de mayor CPU del pool.
- Por debajo del umbral  =>  reanuda despliegues.
- Intervalo: 15 s. Configurable en `agents/config.py`.

## Integracion con la plataforma
- Fichero compartido `/opt/rootpath/runtime` montado en el contenedor CTFd:
  - `deploy_paused` (0/1): leido por el plugin; si esta a 1, `exam/start` responde 503.
  - `monitor_status.json`: estado del monitor, expuesto en `GET /plugins/rootpath/api/status`.
  - `agent_key`: clave compartida; el endpoint interno `GET /plugins/rootpath/api/agent/hint`
    exige `X-Agent-Key` (el tutor lee pistas por aqui, NUNCA flags).

## Comandos utiles
    python3 /opt/rootpath/agents/cli.py monitor read_metrics
    python3 /opt/rootpath/agents/cli.py monitor pool_members
    python3 /opt/rootpath/agents/cli.py tutor get_hint '{"challenge_id":3,"level":3}'
    python3 /opt/rootpath/agents/cli.py curador recommend_next '{"cert_id":1}'
    python3 /opt/rootpath/agents/cli.py audit tail 20
    python3 /opt/rootpath/agents/cli.py audit verify
    systemctl status rootpath-monitor

## Evidencia de aceptacion (monitor sin intervencion)
1. Loadtest (CT113, pool agentmanaged) genera carga: CPU nodo sube a 68.8% (> 60%).
2. El monitor, en su ciclo automatico: read_metrics -> detecta umbral -> stop_guest(113)
   -> alert -> set_deploy_paused(1). Sin intervencion humana.
3. CT113 pasa a `stopped`; `deploy_paused=1`; acciones registradas en audit.jsonl.
4. Cadena de auditoria verificada: `cadena_valida=True`.
5. Con la plataforma en pausa, `exam/start` responde 503; al reanudar, 200.

## Nota de seguridad
El token de Proxmox esta limitado por ACL/pool. Los agentes no ejecutan shell arbitraria:
solo acciones permitidas, implementadas en Python (no hay `pct`/`qm` invocados por el agente).
Para produccion: rotar el token, restringir aun mas el pool y mover el monitor a un nodo dedicado.
