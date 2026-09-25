# -*- coding: utf-8 -*-
"""SaveQuest - Visor de Partidas (Web facil: LFI en el visor de saves)."""
import os
from flask import Flask, render_template, request

SAVES = "/app/saves"
app = Flask(__name__)


@app.route("/")
def index():
    saves = sorted(os.listdir(SAVES)) if os.path.isdir(SAVES) else []
    return render_template("index.html", saves=saves)


@app.route("/ver")
def ver():
    name = request.args.get("save", "slot1.txt")
    path = os.path.join(SAVES, name)  # sin saneo -> traversal
    try:
        with open(path, "r", errors="replace") as fh:
            content = fh.read()[:4000]
    except Exception:
        content = "(archivo no encontrado)"
    return render_template("ver.html", name=name, content=content)


if __name__ == "__main__":
    os.makedirs(SAVES, exist_ok=True)
    for slot, data in [("slot1.txt", "NIVEL 7 · Mazmorra del Dragon · 3 corazones\nobjetos: espada_rota, pocion_verde"),
                       ("slot2.txt", "NIVEL 2 · Bosque Encantado · 6 corazones\nobjetos: mapa, linterna"),
                       ("slot3.txt", "NIVEL 12 · Castillo del Conde · 1 corazon\nobjetos: llave_dorada")]:
        with open(os.path.join(SAVES, slot), "w") as fh:
            fh.write(data)
    app.run(host="0.0.0.0", port=5000)
