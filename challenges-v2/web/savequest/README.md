# Reto Web - SaveQuest (FACIL · 100)

Visor de partidas de un RPG. **LFI** (path traversal) en el parametro `save`.

## Cadena
1. `GET /ver?save=../../flag.txt` -> lee la flag de la raiz del sistema.

## Archivos
`app.py` (`os.path.join` sin saneo), `templates/`, `static/`, `build_easy.sh`, `solve_save.py`.

## Notas
- Los saves viven en `/app/saves`; la flag en `/flag.txt`.
- Flag dinamica por usuario + instancia por usuario.
