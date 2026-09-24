# -*- coding: utf-8 -*-
"""NimbusDrive - almacenamiento en la nube (Web extremo, aleatorizado por instancia).

Cadena: deobfuscar JS -> LFI (config con SIGNING_KEY/INTERNAL_URL/NONCE) ->
firmar HMAC -> SSRF a servicio interno -> inyeccion -> flag.
"""
import os, hmac, hashlib, json
import requests as rq
from flask import Flask, request, render_template, jsonify

SIGNING_KEY = os.environ.get("SIGNING_KEY", "nokey")
BASE = "/data"

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/v2/files/export")
def export():
    name = request.args.get("name", "")
    path = os.path.join(BASE, name)          # sin saneo -> traversal
    try:
        with open(path, "rb") as fh:
            return fh.read()[:20000], 200, {"Content-Type": "text/plain"}
    except Exception as e:
        return "error: %s" % e, 404


@app.route("/admin/reindex", methods=["POST"])
def reindex():
    raw = request.get_data() or b""
    sig = request.headers.get("X-Sign", "")
    expected = hmac.new(SIGNING_KEY.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return {"error": "firma invalida"}, 401
    try:
        d = json.loads(raw or b"{}")
    except Exception:
        return {"error": "json invalido"}, 400
    url = d.get("url", "")
    if not url.startswith(("http://127.0.0.1", "http://localhost")):
        return {"error": "url no permitida"}, 400
    try:
        r = rq.get(url, timeout=6)
        return r.text[:8000], 200, {"Content-Type": "text/plain"}
    except Exception as e:
        return "error: %s" % e, 500


@app.route("/api/v1/status")
def status():
    return jsonify({"app": "NimbusDrive", "version": "2.7.0"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
