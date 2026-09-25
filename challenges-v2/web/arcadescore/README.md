# Reto Web - ArcadeScore (FACIL · 100)

Tabla de puntuaciones de un arcade. Login vulnerable a **SQLi** (concatenacion directa).

## Cadena
1. `POST /login` con `u=admin' --` -> sesion de administrador.
2. `GET /panel` muestra los premios -> flag.

## Archivos
`app.py` (login SQLi + panel), `templates/`, `static/`, `build_easy.sh`, `solve_arcade.py`.

## Notas
- Cuenta de prueba `jugador`/`demo123` visible en la pagina.
- La clave del admin es aleatoria por instancia; el bypass no la necesita.
- Flag dinamica por usuario + instancia por usuario.
