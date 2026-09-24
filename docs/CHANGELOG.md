# Changelog

## 2026-09-24 — Instancias por usuario, flag dinámica y panel

### Añadido
- **Instancias efímeras por usuario**: cada alumno despliega su propio contenedor
  (`rp-<reto>-u<uid>`) en un puerto propio (30000-40000), con límites (256 MB / 0.5 CPU)
  y máximo 3 por usuario.
- **Flag única por usuario** (tipo de flag `rootpath`): `RP{<reto>_<hmac8>}`, inyectada en
  runtime (`RP_FLAG`); web vía `after_request`, Linux en `/root/flag.txt`. No se puede compartir.
- **Autocierre al acertar la flag** (`ok:auto_solve`).
- **Reaper por TTL** (systemd timer cada 30 s) → `ok:auto_ttl`.
- **Landing de bienvenida** (`welcome.html`) con login/registro reales; redirecciones de `/`,
  `/login`, `/register` y sobrescritura de plantillas de auth.
- **Panel administrativo RootPath** (`admin.html`, endpoint `/api/admin/overview`), con
  estadísticas, usuarios, scoreboard, retos y submissions; `/admin` redirige al panel.
- **Auditoría de laboratorios** (`rp_lab_actions`, `rp_lab_instances`) con `user_id` e IP,
  visible solo para admin, con rate-limit.
- **Botón de descarga** de adjuntos en el dashboard (retos estáticos).
- **VPN** restringida a RootPath (Tailscale subnet route + WireGuard).
- **Documentación** completa en `docs/`.
- **Repositorio** privado en GitHub.

### Cambios
- Los retos de servicio ya **no** embeben la flag (builders leídos en runtime).
- Se retiró el modo **compartido** (contenedor único) en favor del modo por usuario.
- `/api/v1/users/me` no se usa para el rol; se añadió `/api/me`.
- Las descripciones de los retos de servicio apuntan a “pulsa Abrir…”

### Corregido
- `NameError` en `app.py` de `web_sqli`.
- URL del endpoint de mapeo (`/plugins/rootpath/api/agent/map`).
- Borrado en cascada de `RootPathMap` (limpieza explícita).
- Páginas CTFd antiguas accesibles (`/cyber-range`) → redirigidas.
- Se purgó `.student_token` del historial de git.

## Fases anteriores
- **Fase 0**: CTFd + 10 retos (challenge-as-code).
- **Fase 2**: plugin (rutas/readiness/modo examen) + UI.
- **Fase 3**: agentes (monitor/curador/tutor) con auditoría encadenada.
- **Fase 4**: pipeline creador → validador → aprobación → publicación.
- **Fase 5**: rutas AD y Blue Team + analíticas.
- **UI**: dashboard Cyber Range, rediseño por carpetas, ocultar menú CTFd.
