# RootPath - Dashboard (UI Cyber Range)

UI standalone integrada como plugin CTFd, accesible en:
    http://172.170.10.11:8000/plugins/rootpath/dashboard
(o desde el menu, pagina "Cyber Range" que redirige).

## Componentes
- Plantilla: plugins/rootpath/templates/dashboard.html (standalone, no usa el tema de CTFd).
- Ruta plugin: GET /plugins/rootpath/dashboard  (requiere sesion; authed_only).
- Endpoint:   GET /plugins/rootpath/api/catalog (retos + pistas desbloqueadas + estado).
- nav.js: script registrado globalmente (fallback; el enlace real va por la pagina CTFd).

## Secciones y datos reales
- Desafios: catalogo completo, detalle, pistas (desbloqueo real), envio de bandera real.
- Rutas: /api/paths (progress + readiness).
- Modo Examen: /api/exam/* (iniciar, informe, finalizar) con cronometro.
- Analiticas: /api/analytics (totales, categorias, retos a revisar, top usuarios).
- Usuarios: top usuarios desde analiticas.
- Panel "Entorno": estado de la plataforma + metricas del monitor (via /api/status) y temporizador de estudio local.

## Notas
- El desbloqueo de pistas usa POST /api/v1/unlocks con type="hints" (nombre de tabla que espera CTFd).
- "Entornos efimeros por usuario" (TTL, VLAN) siguen pendientes: Fase 1.
