# -*- coding: utf-8 -*-
"""Servicio interno de miniaturas de NimbusDrive (solo 127.0.0.1:8080)."""
import os, subprocess
from flask import Flask, request

NONCE = os.environ.get("INTERNAL_NONCE", "")
PATHK = os.environ.get("INTERNAL_PATH", "srv")
app = Flask(__name__)


@app.route("/")
def home():
    return "nimbus-internal"


@app.route("/" + PATHK + "/thumb")
def thumb():
    if request.args.get("nonce") != NONCE:
        return "forbidden", 403
    src = request.args.get("src", "logo.png")
    r = subprocess.run("head -n 40 /data/" + src, shell=True,
                       capture_output=True, text=True, timeout=8)
    return (r.stdout + r.stderr) or "ok"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
