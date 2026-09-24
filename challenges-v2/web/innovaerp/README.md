# Reto Web — InnovaERP (EXTREMO · 200)

Panel corporativo realista (Bootstrap 5) con una **cadena de 4 pasos** hasta RCE.

## Cadena de resolución (no se revela en la descripción)
1. **Source leak**: `GET /static/app.js` filtra `jwt_secret = "innova-changeme"` en un comentario.
2. **JWT débil**: el login usa JWT HS256; con el secreto se **forja** un token con `role: admin`.
3. **Panel admin** (`/panel/integraciones`, requiere admin): filtra el **token del bus interno**.
4. **SSRF → RCE**: el "Probador de Webhooks" (`/api/v1/webhook`) hace peticiones desde el servidor;
   apuntándolo a `http://127.0.0.1:8080/exec?cmd=...` (bus interno, no publicado) con la cabecera
   `X-Internal-Token` se ejecuta **código** → se lee `/flag.txt` (flag dinámica del usuario).

## Servicios en el contenedor
- `app.py`  → Flask en `0.0.0.0:5000` (público).
- `worker.py` → Flask en `127.0.0.1:8080` (bus interno, no expuesto).
- `entrypoint.sh` → escribe `RP_FLAG` en `/flag.txt` y arranca ambos.

## Archivos
- `app.py`, `worker.py`, `entrypoint.sh`, `Dockerfile`, `templates/`, `static/app.js`, `static/app.css`.
- `build_web.sh` → descarga **Bootstrap 5.3** (MIT) y construye la imagen `rootpath-v2-innovaerp-panel`,
  y registra el reto en `runtime/lab_map.json`.
- `solve_web.py` → reproduce la cadena (recibe el puerto por argumento).
- `upd_labmap.py` → añade la entrada al mapa de labs.

## Notas
- Es un reto **de servicio** → **flag dinámica por usuario** (`RP{innovaerp-panel_<hmac8>}`) y se
  despliega como **instancia por usuario** (puerto propio).
- Bootstrap se descarga en el build (no se versiona el CSS grande).
