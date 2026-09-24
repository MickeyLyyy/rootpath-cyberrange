# -*- coding: utf-8 -*-
"""Builders Web (Flask + UI realista). Flag dinamica via env RP_FLAG."""


def _web_df(extra=""):
    return ("FROM python:3.12-slim\n"
            "RUN pip install --no-cache-dir flask==3.0.3\n"
            "WORKDIR /app\n"
            "COPY app.py /app/app.py\n" + extra +
            "EXPOSE 5000\nCMD [\"python\",\"/app/app.py\"]\n")


# Inyecta la flag de runtime: el HTML usa el marcador y se sustituye por RP_FLAG.
_INJ = ("\nimport os as _os\n"
        "RP_FLAG = _os.environ.get(\"RP_FLAG\", \"RP{flag_no_asignada}\")\n"
        "@app.after_request\n"
        "def _rp_inject(resp):\n"
        "    try:\n"
        "        if resp.mimetype == \"text/html\":\n"
        "            resp.set_data(resp.get_data(as_text=True).replace(\"{{RP_FLAG}}\", RP_FLAG))\n"
        "    except Exception:\n"
        "        pass\n"
        "    return resp\n")


def _dyn(app):
    app = app.replace("__FLAG__", "{{RP_FLAG}}")
    app = app.replace("app = Flask(__name__)", "app = Flask(__name__)" + _INJ, 1)
    return app



def _t_web_comment(spec, flag):
    app = '''from flask import Flask
app = Flask(__name__)
@app.route("/")
def tienda():
    return """<!doctype html>
<html lang='es'><head><meta charset='utf-8'><title>Colmado La Esquina del Coro</title>
<!-- TODO(dev): quitar antes de produccion. credencial admin interna: __FLAG__ -->
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial,sans-serif;background:#f6f1e7;color:#2b2b2b}
header{background:#b22222;color:#fff;padding:18px 24px;display:flex;justify-content:space-between;align-items:center}
header h1{font-size:22px}nav a{color:#fff;margin-left:16px;text-decoration:none;font-size:14px}
.hero{background:#fff8e1;padding:28px 24px;border-bottom:1px solid #e0d5b8}.hero h2{font-size:20px;margin-bottom:6px}
.hero p{color:#5b5b5b;font-size:14px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;padding:24px}
.card{background:#fff;border:1px solid #e6dfcd;border-radius:8px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.card h3{font-size:16px;margin-bottom:6px}.card p{font-size:13px;color:#666}.precio{color:#b22222;font-weight:bold;margin-top:8px}
footer{background:#2b2b2b;color:#ccc;padding:16px 24px;font-size:13px;display:flex;justify-content:space-between}
</style></head><body>
<header><h1>Colmado La Esquina del Coro</h1><nav><a href='/'>Inicio</a><a href='#'>Ofertas</a><a href='#'>Recargas</a><a href='#'>Contacto</a></nav></header>
<div class='hero'><h2>Tu colmado de confianza, ahora en linea</h2><p>Viveres, recargas y delivery en la Av. Duarte esq. Paris.</p></div>
<div class='grid'>
<div class='card'><h3>Arroz Selecto 5lb</h3><p>Grano largo, calidad premium.</p><p class='precio'>RD$ 320</p></div>
<div class='card'><h3>Habichuelas Rojas 2lb</h3><p>Ideal para la bandera dominicana.</p><p class='precio'>RD$ 140</p></div>
<div class='card'><h3>Aceite de Soya</h3><p>Botella de 1 litro.</p><p class='precio'>RD$ 180</p></div>
<div class='card'><h3>Recarga de Datos</h3><p>Recarga de RD$ 100.</p><p class='precio'>RD$ 100</p></div>
<div class='card'><h3>Salami</h3><p>El clasico del desayuno.</p><p class='precio'>RD$ 95</p></div>
<div class='card'><h3>Queso de Hoja</h3><p>Fresco del dia.</p><p class='precio'>RD$ 210</p></div>
</div>
<footer><span>Av. Duarte esq. Calle Paris, Santo Domingo</span><span>Horario: 7am - 11pm</span></footer>
</body></html>"""
app.run(host="0.0.0.0", port=5000)
'''
    app = _dyn(app)
    solve = ("#!/usr/bin/env bash\n"
             "curl -s \"http://127.0.0.1:${PORT}/\" | grep -o \"RP{[^}]*}\"\n")
    note = "Inspecciona el codigo fuente (Ctrl+U) y busca el comentario HTML en el <head>."
    return {"Dockerfile": _web_df(), "app.py": app}, solve, \
        {"kind": "service", "internal_port": 5000, "connection": "http://HOST:PORT/"}, note


def _t_web_idor(spec, flag):
    app = '''from flask import Flask
app = Flask(__name__)
TICKETS = {
    0: ("ADMIN", "Ticket interno de administracion. Nota confidencial: __FLAG__"),
    1: ("Maria P.", "Toyota Corolla 2019 - placa G456789 - entrada 08:12"),
    2: ("Juan R.", "Honda Civic 2021 - placa G112233 - entrada 08:40"),
    3: ("Ana L.", "Hyundai Tucson 2020 - placa G998877 - entrada 09:05"),
}
@app.route("/")
def index():
    return """<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Parqueo Boulevard del Este</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial,sans-serif;background:#eef3f7;color:#223}
header{background:#0b5c8a;color:#fff;padding:16px 24px}header h1{font-size:20px}
main{max-width:600px;margin:40px auto;padding:0 20px}.panel{background:#fff;border-radius:10px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
label{display:block;margin-bottom:6px;font-size:14px}input{width:100%;padding:10px;border:1px solid #ccc;border-radius:6px;margin-bottom:14px;font-size:15px}
button{background:#0b5c8a;color:#fff;border:none;padding:10px 18px;border-radius:6px;cursor:pointer;font-size:15px}
.result{margin-top:18px;padding:14px;background:#f4f9fd;border-left:4px solid #0b5c8a;border-radius:4px}
</style></head><body>
<header><h1>Parqueo Boulevard del Este - Higuey</h1></header>
<main><div class='panel'><h2>Consulta tu ticket</h2><p style='font-size:13px;color:#666;margin:6px 0 16px'>Ingresa el numero de ticket para ver el detalle.</p>
<form action='/ticket' method='get'><label>Numero de ticket</label><input name='id' placeholder='ej. 1'><button>Consultar</button></form>
<div class='result'>Usa /ticket/&lt;id&gt; para consultar directamente.</div></div></main></body></html>"""
@app.route("/ticket/<int:tid>")
def ticket(tid):
    t = TICKETS.get(tid)
    if not t:
        return "<h2>Ticket no encontrado</h2>"
    return """<!doctype html><html><head><meta charset='utf-8'><title>Ticket %d</title></head>
<body style='font-family:Arial;max-width:600px;margin:30px auto'><h2 style='color:#0b5c8a'>Ticket #%d</h2>
<p><b>Titular:</b> %s</p><pre style='background:#f4f9fd;padding:14px'>%s</pre>
<p><a href='/'>Volver</a></p></body></html>""" % (tid, tid, t[0], t[1])
app.run(host="0.0.0.0", port=5000)
'''
    app = _dyn(app)
    solve = ("#!/usr/bin/env bash\n"
             "curl -s \"http://127.0.0.1:${PORT}/ticket/0\" | grep -o \"RP{[^}]*}\"\n")
    note = "La URL expone IDs predecibles. El ticket administrativo esta en el ID 0."
    return {"Dockerfile": _web_df(), "app.py": app}, solve, \
        {"kind": "service", "internal_port": 5000, "connection": "http://HOST:PORT/"}, note


def _t_web_sqli(spec, flag):
    app = '''import sqlite3
from flask import Flask, request
app = Flask(__name__)

def db():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE usuarios (usuario TEXT, clave TEXT, nombre TEXT)")
    c.execute("INSERT INTO usuarios VALUES ('admin','Cl4v3_S3cr3ta_2026!','Administrador del portal')")
    c.execute("INSERT INTO usuarios VALUES ('cajero','cajero123','Cajero de sucursal')")
    return c

@app.route("/")
def login():
    u = request.args.get("usuario", "")
    p = request.args.get("clave", "")
    c = db()
    query = "SELECT * FROM usuarios WHERE usuario = '" + u + "' AND clave = '" + p + "'"
    ok = None
    try:
        r = c.execute(query).fetchone()
        if r:
            ok = r
    except Exception:
        ok = None
    body = """
<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Banca del Malecon</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#0f2d4a,#123c63);color:#eaf2fb;min-height:100vh}
header{background:rgba(0,0,0,.25);padding:18px 28px;display:flex;justify-content:space-between;align-items:center}
header .brand{font-size:20px;font-weight:bold}nav a{color:#cfe0f0;margin-left:18px;text-decoration:none;font-size:14px}
.wrap{display:flex;justify-content:center;padding:60px 20px}.card{background:#fff;color:#223;border-radius:12px;padding:32px;width:380px;box-shadow:0 10px 40px rgba(0,0,0,.4)}
.card h2{margin-bottom:4px;font-size:20px}.card .sub{color:#667;font-size:13px;margin-bottom:20px}
label{display:block;font-size:13px;margin:12px 0 4px}input{width:100%;padding:10px;border:1px solid #ccd;border-radius:6px;font-size:14px}
button{width:100%;background:#0f2d4a;color:#fff;border:none;padding:12px;border-radius:6px;margin-top:18px;font-size:15px;cursor:pointer}
.alert{margin-top:16px;padding:12px;border-radius:6px;font-size:13px}
.ok{background:#e6f7ec;color:#157347}.err{background:#fdeaea;color:#b02a2a}
footer{margin-top:30px;text-align:center;color:#9fb6cc;font-size:12px}
</style></head><body>
<header><span class='brand'>Banca del Malecon</span><nav><a href='/'>Inicio</a><a href='#'>Cuentas</a><a href='#'>Soporte</a></nav></header>
<div class='wrap'><div class='card'>
<h2>Acceso a Banca en Linea</h2><p class='sub'>Entidad ficticia de demostracion</p>
<form action='/' method='get'><label>Usuario</label><input name='usuario'><label>Clave</label><input name='clave' type='password'><button>Ingresar</button></form>
__RESULT__
</div></div><footer>Banca del Malecon es una entidad ficticia para fines educativos.</footer></body></html>"""
    if ok:
        res = "<div class='alert ok'>Bienvenido, %s.</div><div class='alert ok'>FLAG: __FLAG__</div>" % ok["nombre"]
    else:
        res = "<div class='alert err'>Usuario o clave incorrectos.</div>"
    return body.replace("__RESULT__", res)
app.run(host="0.0.0.0", port=5000)
'''
    app = _dyn(app)
    solve = ("#!/usr/bin/env bash\n"
             "curl -s -G --data-urlencode \"usuario=admin' OR '1'='1\" --data-urlencode 'clave=x' "
             "\"http://127.0.0.1:${PORT}/\" | grep -o \"RP{[^}]*}\"\n")
    note = "Inyecta en el usuario: admin' OR '1'='1  para devolver la fila de admin sin conocer la clave."
    return {"Dockerfile": _web_df(), "app.py": app}, solve, \
        {"kind": "service", "internal_port": 5000, "connection": "http://HOST:PORT/"}, note


BUILDERS = {
    "web_comment": _t_web_comment,
    "web_idor": _t_web_idor,
    "web_sqli": _t_web_sqli,
}

