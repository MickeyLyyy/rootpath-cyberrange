# Modelo de datos

Tablas del plugin (prefijo `rp_`) en la base de datos de CTFd. Se crean con
`db.create_all()` al cargar el plugin.

## `rp_certifications` (RootPathCert)
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| name | str(128) unique | Ej. "Fundamentos de Pentesting (eJPT)". |
| description | text | |
| weight | float | Peso en el cálculo de readiness. |

## `rp_domains` (RootPathDomain)
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| cert_id | FK → rp_certifications.id | |
| name | str(200) | Ej. "Reconocimiento y Web". |
| weight | float | |

## `rp_challenge_domains` (RootPathMap)
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| challenge_id | FK → challenges.id (CASCADE) | |
| domain_id | FK → rp_domains.id (CASCADE) | |

## `rp_exam_sessions` (RootPathExam)
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| user_id | int | |
| cert_id | int null | |
| started / ends / finished | datetime | Cronómetro e informe. |
| status | str(32) | `active` / `finished` / `expired`. |
| challenge_ids | text | CSV de retos del examen. |
| report | largebinary | Informe final. |

## `rp_lab_actions` (RootPathLabAction) — auditoría
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| created_at | datetime | UTC. |
| user_id / user_name | int / str | Identidad única del actor. |
| ip | str(64) | IP de origen (XFF si hay proxy). |
| forwarded_for / user_agent | str | Contexto. |
| action | str(16) | `start` / `stop` / `restart`. |
| challenge_name / service | str | Reto y servicio. |
| result | str(32) | `ok`, `ok:auto_ttl`, `ok:auto_solve`, `error:*`, `denied:*`. |
| detail | text | Salida de docker. |

## `rp_lab_instances` (RootPathLabInstance) — instancias activas
| Columna | Tipo | Notas |
|---|---|---|
| id | int PK | |
| user_id / user_name | int / str | Dueño de la instancia. |
| challenge_id / challenge_name | int / str | Reto. |
| service / image | str | Servicio e imagen docker. |
| container_name | str | `rp-<service>-u<uid>`. |
| host_port / internal_port | int | Puerto publicado en el LXC / interno. |
| kind | str(16) | `web` / `linux`. |
| created_at / expires_at | datetime | TTL. |
| status | str(16) | `running`. |

> Única por `(user_id, challenge_id)`.

## `rp_lab_leases` (RootPathLabLease) — *legacy*
Modelo del modo **compartido** anterior (un contenedor por reto). Se conserva por
compatibilidad; el modo actual es **por usuario** (`rp_lab_instances`).

## Flags (CTFd `flags`) — tipo `rootpath`
Los retos de servicio usan `type="rootpath"` con `content=<slug>`. El valor esperado se
calcula por usuario: `RP{<slug>_<8 hex de HMAC-SHA256(flag_secret, user_id, challenge_id)>}`.
Ver `plugins/rootpath/flags.py`.
