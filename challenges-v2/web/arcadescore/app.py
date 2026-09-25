# -*- coding: utf-8 -*-
"""ArcadeScore - Tabla de Puntuaciones (Web facil: SQLi en login)."""
import os, sqlite3, secrets
from flask import Flask, request, render_template, session, redirect

DB = "/app/data/arcade.db"
app = Flask(__name__)
app.secret_key = "arcade-scoreboard-2026"


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


@app.route("/")
def index():
    with db() as c:
        scores = c.execute("SELECT * FROM scores ORDER BY puntos DESC").fetchall()
    return render_template("index.html", scores=scores,
                           error=request.args.get("error"))


@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("u", "")
    p = request.form.get("p", "")
    # vulnerable a proposito: concatenacion directa en la consulta
    q = "SELECT * FROM users WHERE username='%s' AND password='%s'" % (u, p)
    with db() as c:
        row = c.execute(q).fetchone()
    if not row:
        return redirect("/?error=credenciales+invalidas")
    session["user"] = row["username"]
    session["rol"] = row["rol"]
    return redirect("/panel")


@app.route("/panel")
def panel():
    if not session.get("user"):
        return redirect("/")
    if session.get("rol") != "admin":
        return render_template("panel.html", user=session["user"], admin=False)
    flag = open("/flag.txt").read().strip()
    return render_template("panel.html", user=session["user"], admin=True, flag=flag)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    os.makedirs("/app/data", exist_ok=True)
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, rol TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS scores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jugador TEXT, juego TEXT, puntos INTEGER)""")
        c.execute("INSERT OR IGNORE INTO users(username,password,rol) "
                  "VALUES('admin', ?, 'admin')", (secrets.token_hex(8),))
        c.execute("INSERT OR IGNORE INTO users(username,password,rol) "
                  "VALUES('jugador', 'demo123', 'jugador')")
        for j, g, pts in [("El_Tiguerazo", "Pac-Man", 333360),
                          ("MegaDama", "Galaga", 210450),
                          ("DonkeyRD", "Donkey Kong", 128800),
                          ("FantaZero", "Tetris", 99999),
                          ("PixelPlatano", "Space Invaders", 45600),
                          ("CocoloWifi", "Frogger", 22210)]:
            c.execute("INSERT OR IGNORE INTO scores(jugador,juego,puntos) "
                      "VALUES(?,?,?)", (j, g, pts))
        c.commit()
    app.run(host="0.0.0.0", port=5000)
