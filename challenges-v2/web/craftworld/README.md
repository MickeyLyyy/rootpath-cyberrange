# Reto Web - CraftWorld (FACIL · 150)

Panel de administracion de un servidor de supervivencia. **Inyeccion de comandos** en la herramienta de diagnostico.

## Cadena
1. `POST /ping` con `host=127.0.0.1; cat /flag.txt` -> ejecucion en la shell.

## Archivos
`app.py` (`subprocess.run(..., shell=True)` sin validar), `templates/`, `static/`, `build_easy.sh`, `solve_craft.py`.

## Notas
- `iputils-ping` instalado para que el diagnostico sea realista.
- Flag dinamica por usuario + instancia por usuario.
