# -*- coding: utf-8 -*-
"""Colmado - panel de diagnostico (maquina boot2root).

Servicio web con inyeccion de comandos. Corre como el usuario 'player'.
El objetivo es obtener shell, escalar privilegios y leer /root/flag.txt.
"""
from flask import Flask, request
import subprocess

app = Flask(__name__)


@app.route("/")
def index():
    return ("<h1>Colmado - Panel de diagnostico</h1>"
            "<p>Herramienta de red del colmado online.</p>"
            "<p>Uso: <code>/ping?host=127.0.0.1</code></p>")


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    out = subprocess.run("ping -c 1 " + host, shell=True,
                         capture_output=True, text=True, timeout=10)
    return "<pre>" + (out.stdout + out.stderr) + "</pre>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
