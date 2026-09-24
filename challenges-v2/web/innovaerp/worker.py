# -*- coding: utf-8 -*-
"""Bus interno de InnovaERP (solo 127.0.0.1:8080)."""
import os, subprocess
from flask import Flask, request

TOKEN = os.environ.get("INTERNAL_TOKEN", "innova-bus-2026")
app = Flask(__name__)


@app.route("/")
def home():
    return "innova-bus ok"


@app.route("/health")
def health():
    return {"status": "ok", "service": "innova-bus"}


@app.route("/exec")
def exe():
    if request.headers.get("X-Internal-Token") != TOKEN:
        return "forbidden", 403
    cmd = request.args.get("cmd", "id")
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8)
        return (out.stdout or out.stderr or "(sin salida)")
    except Exception as e:
        return "error: %s" % e, 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
