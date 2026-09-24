# -*- coding: utf-8 -*-
"""InnovaERP - panel corporativo (reto Web extremo).

Cadena: source leak (JWT secret) -> forjar JWT admin -> SSRF (webhook) ->
servicio interno (RCE) -> flag.
"""
import os, datetime
import jwt
import requests as rq
from functools import wraps
from flask import (Flask, request, redirect, make_response, render_template,
                   jsonify, abort)

FLAG = os.environ.get("RP_FLAG", "RP{noflag}")
JWT_SECRET = "innova-changeme"          # leak en static/js/app.js
INTERNAL = "http://127.0.0.1:8080"
USERS = {"jperez": "Jp2026$demo", "mlopez": "Ml0pez!26"}

app = Flask(__name__)
app.secret_key = os.urandom(16)


def token_for(user, role):
    payload = {"user": user, "role": role,
               "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=4)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current():
    t = request.cookies.get("session_token")
    if not t:
        return None
    try:
        return jwt.decode(t, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None


def require(role=None):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            u = current()
            if not u:
                return redirect("/login")
            if role and u.get("role") != role:
                return render_template("403.html", user=u), 403
            return f(*a, **k)
        return w
    return deco


@app.route("/")
def index():
    return redirect("/panel")


@app.route("/robots.txt")
def robots():
    return ("User-agent: *\nDisallow: /panel/\nDisallow: /api/\nDisallow: /static/js/\n")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("usuario", "")
        p = request.form.get("clave", "")
        if u in USERS and USERS[u] == p:
            r = make_response(redirect("/panel"))
            r.set_cookie("session_token", token_for(u, "user"), httponly=False)
            return r
        return render_template("login.html", error="Credenciales invalidas"), 200
    return render_template("login.html")


@app.route("/logout")
def logout():
    r = make_response(redirect("/login"))
    r.delete_cookie("session_token")
    return r


@app.route("/panel")
@require()
def panel():
    return render_template("dashboard.html", user=current())


@app.route("/panel/clientes")
@require()
def clientes():
    return render_template("clientes.html", user=current())


@app.route("/panel/integraciones")
@require("admin")
def integraciones():
    # token del bus interno (queda en el HTML para el admin)
    internal_token = os.environ.get("INTERNAL_TOKEN", "innova-bus-2026")
    return render_template("integraciones.html", user=current(),
                           internal=INTERNAL, token=internal_token)


@app.route("/api/v1/status")
def status():
    return jsonify({"app": "InnovaERP", "version": "3.4.1", "env": "prod"})


@app.route("/api/v1/webhook", methods=["POST"])
@require("admin")
def webhook():
    d = request.get_json(silent=True) or {}
    url = d.get("url", "")
    headers = d.get("headers", {}) or {}
    try:
        r = rq.get(url, headers=headers, timeout=6)
        return r.text[:8000], 200, {"Content-Type": "text/plain"}
    except Exception as e:
        return "Error al conectar: %s" % e, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
