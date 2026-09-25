# -*- coding: utf-8 -*-
"""SkinShop - Tienda de Skins (Web facil: IDOR en el detalle de articulos)."""
from flask import Flask, render_template, jsonify

FLAG_PATH = "/flag.txt"

ITEMS = [
    {"id": 1, "name": "Skin Comando", "price": 250, "icon": "&#128170;",
     "desc": "Camuflaje militar clasico."},
    {"id": 2, "name": "Skin Neón", "price": 400, "icon": "&#127762;",
     "desc": "Brilla en la oscuridad del mapa."},
    {"id": 3, "name": "Skin Plátano", "price": 150, "icon": "&#127820;",
     "desc": "La favorita del servidor RD."},
    {"id": 4, "name": "Skin Merenguera", "price": 600, "icon": "&#127926;",
     "desc": "Con sombrero y todo."},
    {"id": 5, "name": "Skin Concho", "price": 300, "icon": "&#128663;",
     "desc": "Rapida y ruidosa."},
    {"id": 6, "name": "Skin Tiburón", "price": 550, "icon": "&#129416;",
     "desc": "Para dominar el modo playa."},
    {"id": 7, "name": "Skin Rey del Colmado", "price": 700, "icon": "&#129346;",
     "desc": "Atiende el counter como un jefe."},
    {"id": 8, "name": "Skin Apagón", "price": 999, "icon": "&#127769;",
     "desc": "Tan oscura como un lunes de EDQ."},
]

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", items=ITEMS)


@app.route("/item/<int:iid>")
def item(iid):
    hidden = [{"id": 9, "name": "Skin Legendaria",
               "price": 999999, "icon": "&#127775;",
               "desc": "Secreto del almacen: %s" % open(FLAG_PATH).read().strip()}]
    for it in ITEMS + hidden:
        if it["id"] == iid:
            return jsonify(it)
    return jsonify({"error": "articulo no existe"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
