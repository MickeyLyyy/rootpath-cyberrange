# API — Referencia

Base del plugin: `/plugins/rootpath` (blueprint CTFd).
`@authed_only` = requiere sesión; `@admins_only` = admin; `público` = sin sesión.

## Páginas
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/plugins/rootpath/welcome` | público | Landing (login/registro). Si hay sesión → redirige al dashboard. |
| GET | `/plugins/rootpath/dashboard` | authed | Dashboard del usuario (SPA). |
| GET | `/plugins/rootpath/admin` | admin | Panel administrativo RootPath. |

## Usuario / catálogo
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/ping` | — | Healthcheck del plugin. |
| GET | `/api/me` | authed | `{admin, id, name, email}` del usuario actual. |
| GET | `/api/catalog` | authed | Retos con pistas, estado y **archivos** (`files: [{name,url}]`). |
| GET | `/api/paths` | — | Rutas (cert/dominio) con readiness del usuario. |
| GET | `/api/readiness` | — | Solo readiness por certificación. |
| GET | `/api/analytics` | authed | Totales, categorías, retos difíciles, top usuarios. |
| GET | `/api/status` | — | Estado de la plataforma (monitor, `deploy_paused`). |

## Modo examen
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/exam/status` | authed | Examen activo, restantes, retos. |
| POST | `/api/exam/start` | authed | `{cert_id?, duration_minutes}`. 503 si `deploy_paused=1`. |
| POST | `/api/exam/report` | authed | `{content}` guarda borrador. |
| POST | `/api/exam/finish` | authed | `{report}` entrega y finaliza. |

## Laboratorios (instancias por usuario)
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/lab/status?name=<reto>` | authed | Estado de **tu** instancia: `{configured, deployed, running, host_port, connection, remaining, ttl_minutes}`. |
| POST | `/api/lab/control` | authed | `{name, action: start\|stop\|restart}`. `start` despliega tu instancia; `stop` la destruye; `restart` la recrea. |
| GET | `/api/lab/audit` | admin | Historial (filtros `user_id`,`action`,`challenge`,`result`,`limit`). |

## Admin
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/admin/overview` | admin | Datos agregados del panel (stats, usuarios, retos, scoreboard, submissions, matriz). |

## Integración con agentes (requieren `X-Agent-Key`)
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/agent/hint?challenge_id=&level=` | Devuelve una pista (el tutor; nunca la flag). |
| POST | `/api/agent/map` | `{challenge_name, domain_name}` → mapea reto↔dominio. |
| GET/POST | `/api/agent/reap` | Destruye instancias con TTL expirado. |

---

# lab_service (`http://172.170.10.11:9001`)

Servicio HTTP (systemd `rootpath-lab`) protegido por cabecera `X-Agent-Key`.

| Método | Ruta | Cuerpo | Descripción |
|---|---|---|---|
| GET | `/lab/status?name=&uid=` | — | `{container, running, states}`. |
| POST | `/lab/deploy` | `{name, uid, host_port, flag}` | `docker run` de la instancia (`rp-<service>-u<uid>`), puerto `host_port`→`internal_port`, `RP_FLAG`. |
| POST | `/lab/destroy` | `{name, uid, container?}` | `docker rm -f` de la instancia. |

Allowlist en `runtime/lab_map.json`; valida `host_port` dentro de 30000-40000.

## Variables de entorno en las instancias
| Variable | Efecto |
|---|---|
| `RP_FLAG` | Flag única del usuario; la inyecta cada reto (web en HTML, Linux en `/root/flag.txt`). |
