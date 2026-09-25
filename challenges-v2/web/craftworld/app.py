# -*- coding: utf-8 -*-
"""CraftWorld - Panel del Servidor (Web facil: inyeccion de comandos en ping)."""
import subprocess
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", out=None)


@app.route("/ping", methods=["POST"])
def ping():
    host = request.form.get("host", "").strip()
    try:
        # diagnostico del servidor: pasa directo a la shell
        r = subprocess.run("ping -c 2 " + host, shell=True,
                           capture_output=True, text=True, timeout=8)
        out = r.stdout + r.stderr
    except Exception as e:
        out = "error: %s" % e
    return render_template("index.html", out=out)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
