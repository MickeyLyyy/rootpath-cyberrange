# RootPath - Fase 2 (Rutas, pistas, modo examen, readiness)

## Componente nuevo: plugin CTFd `rootpath`
Vive en `/opt/rootpath/plugins/rootpath` (en el LXC 112) y se monta en el
contenedor CTFd en `/opt/CTFd/CTFd/plugins/rootpath` (persistente).

### Endpoints (JSON)
- GET  /plugins/rootpath/api/paths       -> rutas: certificaciones, dominios, retos y progreso
- GET  /plugins/rootpath/api/readiness   -> readiness score por certificacion
- GET  /plugins/rootpath/api/exam/status -> estado del simulacro (tiempo, retos, informe)
- POST /plugins/rootpath/api/exam/start  -> inicia simulacro {cert_id?, duration_minutes}
- POST /plugins/rootpath/api/exam/report -> guarda borrador de informe {content}
- POST /plugins/rootpath/api/exam/finish -> finaliza y entrega informe {report}

Nota: en CTFd 3.8 el `Authorization: Token` solo se procesa si la peticion es JSON,
asi que para llamadas por token hay que enviar `Content-Type: application/json`.

## Paginas CTFd (visibles en el menu)
- /rutas         -> Rutas por certificacion (progreso + readiness)
- /modo-examen   -> Simulacro cronometrado con informe
- /writeup-template -> Plantilla de writeups

## Rutas sembradas (seed_certs.py)
1. Fundamentos de Pentesting (eJPT): Reconocimiento y Web, Explotacion Linux, Cripto/Forense
2. Pentesting Intermedio (PNPT): Web avanzada, Post-explotacion Linux, AD (vacio)
3. Seguridad General (Security+): Criptografia, Forense, Seguridad Web

## Readiness score
Por dominio: fraccion de retos resueltos, ponderando 1.0 si se resuelve sin pistas
y 0.7 si se uso alguna. Por certificacion: media ponderada de sus dominios (peso).
Escala 0-100.

## Pistas (3 niveles)
Cada reto tiene 3 pistas con coste creciente (5 / 15 / 30 puntos): orientacion,
tecnica y casi-solucion. Sembradas con seed_hints.py.

## Modo examen
- Sesion cronometrada (por defecto 180 min) sobre los retos de una certificacion.
- Pistas DESHABILITADAS a nivel de servidor durante el examen (403 en /api/v1/unlocks).
- Informe final en Markdown guardado en la tabla rp_exam_sessions.report.
- Acepta un unico examen activo por usuario.

## Tablas (en la BD de CTFd)
rp_certifications, rp_domains, rp_challenge_domains, rp_exam_sessions.

## Resembrar
    docker cp /opt/rootpath/scripts/seed_certs.py rootpath-platform-ctfd-1:/tmp/
    docker cp /opt/rootpath/scripts/seed_hints.py rootpath-platform-ctfd-1:/tmp/
    docker compose exec -T -w /opt/CTFd -e PYTHONPATH=/opt/CTFd ctfd python /tmp/seed_certs.py
    docker compose exec -T -w /opt/CTFd -e PYTHONPATH=/opt/CTFd ctfd python /tmp/seed_hints.py
