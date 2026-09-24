# Reto Web — NimbusDrive (EXTREMO · 200)

Almacenamiento en la nube (Bootstrap 5) con **secretos aleatorios por instancia** y una
cadena de 3 pasos pensada para **no ser resoluble "a ojo"** (requiere deobfuscar, LFI, firmar HMAC y SSRF).

## Cadena
1. **Deobfuscar** `GET /static/app.js`: los endpoints están en **base64** (helper `_d("...")`).
   Reconstruir: `/api/v2/files/export`, `/admin/reindex`, `/app/config/app.env`, `X-Sign`.
2. **LFI**: `/api/v2/files/export?name=../../app/config/app.env` (sin saneo de rutas) →
   `SIGNING_KEY`, `INTERNAL_URL` (con **ruta aleatoria**), `INTERNAL_NONCE`.
3. **HMAC + SSRF**: `/admin/reindex` exige `X-Sign = hex(HMAC-SHA256(SIGNING_KEY, body))`.
   Firmar un `body` con `{"url": INTERNAL_URL + "?src=x;cat /flag.txt&nonce=<NONCE>"}` →
   el servicio interno ejecuta `head -n 40 /data/<src>` (inyección por `;`) → **flag**.

## Aleatorización por instancia (clave anti-AI)
`entrypoint.sh` genera en cada arranque: `SIGNING_KEY`, `INTERNAL_NONCE` y `INTERNAL_PATH`
(ruta del servicio interno). **Ningún writeup estático sirve**; hay que extraerlos de la instancia.

## Archivos
- `app.py` (Flask 5000, LFI + `/admin/reindex` firmado), `renderer.py` (interno `127.0.0.1:8080`),
  `entrypoint.sh` (secretos aleatorios + `/flag.txt`), `Dockerfile`, `templates/`, `static/app.js|.css`.
- `build_nimbus.sh` (Bootstrap + imagen + `lab_map`), `solve_nimbus.py`, `upd_labmap_nimbus.py`.

## Notas
- Reto **de servicio** → **flag dinámica por usuario** + **instancia por usuario**.
- El SSRF en `/admin/reindex` está limitado a `http://127.0.0.1` / `localhost`.
