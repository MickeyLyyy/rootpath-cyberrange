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

## Actualizacion: botones funcionales + UI unica
- Botones Abrir/Parar/Reiniciar = control REAL del contenedor del reto:
  - Plugin: POST /plugins/rootpath/api/lab/control {name, action:start|stop|restart}
  - Estado:  GET /plugins/rootpath/api/lab/status?name=...
  - Backend: servicio systemd `rootpath-lab` (puerto 9001, protegido por X-Agent-Key),
    allowlist en runtime/lab_map.json (reto -> servicio docker).
- Retos sin servicio (estaticos, AD, Blue) -> botones deshabilitados ("sin servicio").
- Aterrizaje: al estar autenticado, `/` redirige al dashboard.
- UI unica: ocultas las paginas antiguas (rutas, modo-examen, analiticas, writeup-template, index);
  unica pagina visible: "Cyber Range".
