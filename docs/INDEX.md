# RootPath — Documentación

Índice de la documentación técnica y operativa del proyecto.

| Documento | Contenido |
|---|---|
| [ARQUITECTURA.md](ARQUITECTURA.md) | Visión general, topología, componentes y flujo de una petición. |
| [INSTALACION.md](INSTALACION.md) | Puesta en marcha desde cero (CTFd, plugin, servicios systemd, VPN). |
| [OPERACION.md](OPERACION.md) | Tareas del día a día: desplegar retos, gestionar instancias, auditoría, backups. |
| [API.md](API.md) | Referencia de endpoints del plugin y del lab_service. |
| [MODELO_DATOS.md](MODELO_DATOS.md) | Tablas (`rp_*`) y modelos. |
| [RETOS_PIPELINE.md](RETOS_PIPELINE.md) | Generador de retos (challenge-as-code), plantillas y specs. |
| [VPN.md](VPN.md) | Acceso remoto con Tailscale y WireGuard, restringido a RootPath. |
| [SEGURIDAD.md](SEGURIDAD.md) | Secretos, aislamiento de instancias, permisos y endurecimiento. |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Problemas comunes y cómo resolverlos. |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios relevantes. |

> Fases históricas del proyecto: [FASE2.md](FASE2.md) … [FASE5.md](FASE5.md), [DASHBOARD.md](DASHBOARD.md), [OPERACION.md](OPERACION.md).

## Resumen en una línea
RootPath es una plataforma CTFd con **retos challenge-as-code** que se despliegan como **instancias efímeras por usuario** (contenedor propio + puerto propio + **flag única por usuario**), accesible por web/SSH y por **VPN restringida a solo RootPath**.
