# Retos — Pipeline (challenge-as-code)

Directorio: `/opt/rootpath/challenges-v2/`

| Archivo | Rol |
|---|---|
| `specs.py` | Definición de los 18 retos (slug, título, categoría, dificultad, plantilla, cert/dominio, narrativa, pistas, parámetros). |
| `tpl_util.py` | Utilidades: `gen_flag()`, `render_docs()`, `PTS`, `DIFF_NAME`. |
| `tpl_web.py`, `tpl_linux.py`, `tpl_crypto.py`, `tpl_forensics.py`, `tpl_ad.py`, `tpl_blue.py` | Builders por tipo (generan `app.py`/`Dockerfile`/artefactos + `solve.sh` + pistas). |
| `run.py` | Orquestador: `generate` / `reset` / `load`. |
| `validate.py` | Despliega y comprueba retos con `solve.sh` (+ chequeos negativos). |
| `load.py` | Publica en CTFd (reto+flag+hints+adjuntos) y mapea cert/dominio. |
| `build/` | **Generado** (no versionado): Dockerfiles, app.py, manifest.json, docker-compose.yml. |

## Tipos de reto
- **service**: contenedor (Web Flask o Linux SSH). Se despliega como **instancia por usuario**.
- **static**: adjunto (crypto/forensics/AD/blue) — flag estática, sin contenedor.

## Categorías y dificultad
Web, Linux, AD, Blue, Crypto, Forensics. Dificultad → puntos: fácil 50, medio 100, difícil 200.

## Comandos
```bash
cd /opt/rootpath/challenges-v2
python3 run.py generate     # escribe build/ y manifest.json
python3 run.py reset        # borra retos en CTFd (API) y baja compos
python3 run.py load         # crea/actualiza retos, flags, hints, adjuntos y mapeos
python3 run.py validate     # deploy + solve.sh + negativos
docker compose -f build/docker-compose.yml build
```

## Flag dinámica por usuario (retos de servicio)
- Las plantillas **no** embeben la flag: las apps Web la inyectan en runtime desde `RP_FLAG`
  (vía un `after_request`), y los Linux escriben `RP_FLAG` en `/root/flag.txt` en el entrypoint.
- Al desplegar, el plugin pasa `RP_FLAG = RP{<slug>_<hmac8(user,reto)>}`.
- CTFd valida con el tipo `rootpath`.

## Adjuntos estáticos
`load.py` sube el archivo del reto a CTFd (`/api/v1/files`). El dashboard los muestra en la
tarjeta **Archivos del reto** con botón **Descargar** (`/files/<location>`).

## Añadir un reto
1. Añadir una entrada en `specs.py`.
2. Crear/ajustar su builder en `tpl_<cat>.py` (o reutilizar plantilla).
3. `run.py generate` → `docker compose build` → `run.py load`.
4. Añadir su servicio (si es `service`) a `runtime/lab_map.json`.

## Aislamiento de las instancias
`lab_service` ejecuta `docker run` con `--memory 256m --cpus 0.5`, sin montajes del host,
en el puerto asignado. Ver [SEGURIDAD.md](SEGURIDAD.md).
