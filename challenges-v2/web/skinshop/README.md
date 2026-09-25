# Reto Web - SkinShop (FACIL · 100)

Tienda de skins de un battle royale. **IDOR** en el detalle de articulos.

## Cadena
1. El catalogo muestra los articulos 1-8.
2. `GET /item/9` -> articulo oculto cuya descripcion contiene la flag.

## Archivos
`app.py` (endpoint `/item/<id>` sin control), `templates/`, `static/`, `build_easy.sh`, `solve_skins.py`.

## Notas
- Pista en el HTML: `<!-- depuracion: el almacen tiene 9 referencias -->`.
- Flag dinamica por usuario + instancia por usuario.
