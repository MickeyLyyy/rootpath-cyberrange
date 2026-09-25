# -*- coding: utf-8 -*-
"""RootPath Bot - responde preguntas sobre los servicios por Telegram."""
import os, re, json, time, socket, http.client
import requests
import pymysql

TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED = {c.strip() for c in os.environ.get("ALLOWED_CHAT", "").split(",") if c.strip()}
DB = dict(host=os.environ.get("DB_HOST", "rootpath-platform-db-1"),
          port=int(os.environ.get("DB_PORT", "3306")),
          user=os.environ.get("DB_USER", "root"),
          password=os.environ.get("DB_PASS", ""),
          database=os.environ.get("DB_NAME", "ctfd"))
PROM = os.environ.get("PROM_URL", "http://prometheus:9090")
SOCK = os.environ.get("DOCKER_SOCK", "/var/run/docker.sock")
TG = "https://api.telegram.org/bot" + TOKEN


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def db(sql):
    con = pymysql.connect(**DB, connect_timeout=5, read_timeout=8)
    try:
        with con.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        con.close()


def prom(expr):
    try:
        r = requests.get(PROM + "/api/v1/query", params={"query": expr}, timeout=8).json()
        res = r.get("data", {}).get("result", [])
        return res
    except Exception:
        return []


def scalar(expr, default=None):
    res = prom(expr)
    if not res:
        return default
    try:
        f = float(res[0]["value"][1])
        return int(f) if f == int(f) else round(f, 1)
    except Exception:
        return default


class _UnixHTTP(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("localhost")
        self._path = path

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        self.sock = s


def docker_containers():
    try:
        c = _UnixHTTP(SOCK)
        c.request("GET", "/containers/json?all=1")
        return json.loads(c.getresponse().read())
    except Exception:
        return []


# ---------------- respuestas ----------------
def help_text():
    return ("🤖 <b>RootPath Bot</b>\n"
            "Pregunta lo que quieras sobre los servicios. Comandos:\n"
            "/estado · /contenedores · /instancias · /retos · /usuarios · "
            "/solves · /puertos · /host · /acciones · /ayuda\n\n"
            "También entiendo frases: <i>\"cpu del nodo\"</i>, "
            "<i>\"cuántos contenedores\"</i>, <i>\"qué retos hay\"</i>...")


def c_estado():
    cpu = scalar('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))*100)', "?")
    ram = scalar("(1 - node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes)*100", "?")
    inst = scalar("rootpath_instances_active", "?")
    users = db("SELECT COUNT(*) FROM users")[0][0]
    solves = db("SELECT COUNT(*) FROM solves")[0][0]
    running = sum(1 for c in docker_containers() if c.get("State") == "running")
    return ("📊 <b>Estado RootPath</b>\n"
            f"• Nodo: CPU {cpu}% · RAM {ram}%\n"
            f"• Contenedores en marcha: {running}\n"
            f"• Instancias de lab: {inst}\n"
            f"• Usuarios: {users} · Resoluciones: {solves}")


def c_contenedores():
    cs = docker_containers()
    def nm(c):
        return c["Names"][0].lstrip("/")
    lab = [c for c in cs if nm(c).startswith("rp-") and not nm(c).startswith("rp-mon-")]
    mon = [c for c in cs if nm(c).startswith("rp-mon-")]
    plat = [c for c in cs if not nm(c).startswith("rp-")]
    out = [f"🐳 <b>Contenedores ({len(cs)})</b>"]
    out.append(f"<b>Laboratorios ({len(lab)}):</b>")
    if lab:
        for c in sorted(lab, key=nm):
            n = nm(c)
            lb = c.get("Labels", {}) or {}
            reto = lb.get("rootpath.challenge", "-")
            kind = lb.get("rootpath.kind", "-")
            role = lb.get("rootpath.role", "")
            uid = lb.get("rootpath.user", "-")
            role = f"/{role}" if role else ""
            out.append(f"• <code>{esc(n)}</code> [{esc(kind)}{role}] {esc(c.get('State'))} · "
                       f"reto: {esc(reto)} · user {esc(uid)}")
    else:
        out.append("<i>Sin instancias de laboratorio activas.</i>")
    out.append(f"<b>Plataforma:</b> {len(plat)} · <b>Monitoring:</b> {len(mon)}")
    return "\n".join(out)


def c_instancias():
    rows = db("SELECT user_name, challenge_name, service, host_port, kind "
              "FROM rp_lab_instances ORDER BY id DESC")
    out = [f"🧪 <b>Instancias activas ({len(rows)})</b>"]
    for u, ch, svc, port, kind in rows:
        out.append(f"• {esc(u)} · {esc(ch)} · {esc(svc)} · :{port} ({esc(kind)})")
    if not rows:
        out.append("<i>Ninguna en este momento.</i>")
    return "\n".join(out)


def c_retos():
    rows = db("SELECT COALESCE(category,'?'), COUNT(*) FROM challenges GROUP BY category ORDER BY 2 DESC")
    total = sum(r[1] for r in rows)
    out = [f"📚 <b>Retos: {total}</b>"]
    for cat, n in rows:
        out.append(f"• {esc(cat)}: {n}")
    return "\n".join(out)


def c_usuarios():
    total = db("SELECT COUNT(*) FROM users")[0][0]
    top = db("SELECT u.name, COALESCE(SUM(c.value),0) pts FROM users u "
             "LEFT JOIN solves s ON s.user_id=u.id LEFT JOIN challenges c ON c.id=s.challenge_id "
             "GROUP BY u.id ORDER BY pts DESC LIMIT 5")
    out = [f"👥 <b>Usuarios: {total}</b>", "<b>Top puntuación:</b>"]
    for name, pts in top:
        out.append(f"• {esc(name)}: {pts} pts")
    return "\n".join(out)


def c_solves():
    s = db("SELECT COUNT(*) FROM solves")[0][0]
    sub = db("SELECT COUNT(*) FROM submissions")[0][0]
    corr = db("SELECT COUNT(*) FROM submissions WHERE type='correct'")[0][0]
    return (f"✅ <b>Resoluciones: {s}</b>\n"
            f"• Submissions: {sub} ({corr} correctas)")


def c_puertos():
    used = db("SELECT COUNT(*) FROM rp_lab_instances WHERE host_port IS NOT NULL")[0][0]
    return (f"🔌 <b>Puertos de laboratorio</b>\n"
            f"• Asignados: {used} (rango 30000-40000)")


def c_host():
    cpu = scalar('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))*100)', "?")
    ram = scalar("(1 - node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes)*100", "?")
    disk = scalar('(1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs"}'
                  '/node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs"})*100', "?")
    load = scalar("node_load1", "?")
    return ("🖥️ <b>Nodo</b>\n"
            f"• CPU: {cpu}%\n• RAM: {ram}%\n• Disco: {disk}%\n• Load (1m): {load}")


def c_acciones():
    rows = db("SELECT user_name, action, challenge_name, result, created_at "
              "FROM rp_lab_actions ORDER BY id DESC LIMIT 8")
    out = ["📋 <b>Acciones recientes</b>"]
    for u, a, ch, res, ts in rows:
        when = str(ts)[:19] if ts else "-"
        out.append(f"• {when} · {esc(u)} · {esc(a)} · {esc(ch)} → {esc(res)}")
    if not rows:
        out.append("<i>Sin acciones registradas.</i>")
    return "\n".join(out)


def answer(text):
    t = (text or "").lower()
    if re.search(r"\b(ayuda|help|comandos|start|hola|buenas)\b", t):
        return help_text()
    if re.search(r"\b(estado|status|resumen|summary|como va)\b", t):
        return c_estado()
    if re.search(r"\b(contenedor|contenedores|container|containers|docker|servicio|servicios)\b", t):
        return c_contenedores()
    if re.search(r"\b(instancia|instancias|lab|labs|laboratorio|laboratorios)\b", t):
        return c_instancias()
    if re.search(r"\b(reto|retos|desafio|desafios|challenge|challenges|catalogo)\b", t):
        return c_retos()
    if re.search(r"\b(puerto|puertos|port|ports)\b", t):
        return c_puertos()
    if re.search(r"\b(usuario|usuarios|user|users|jugador|jugadores|ranking|top)\b", t):
        return c_usuarios()
    if re.search(r"\b(solve|solves|resuel|resolucion|resoluciones|flag)\b", t):
        return c_solves()
    if re.search(r"\b(cpu|ram|memoria|disco|host|nodo|nodo|carga|load|recursos)\b", t):
        return c_host()
    if re.search(r"\b(accion|acciones|auditoria|deploy|deploys|denegad|log)\b", t):
        return c_acciones()
    return ("No te he entendido. Prueba <b>/estado</b>, <b>/contenedores</b>, "
            "<b>/retos</b>, <b>/usuarios</b> o escribe <b>/ayuda</b>.")


def send(chat, text):
    try:
        requests.post(TG + "/sendMessage", data={
            "chat_id": chat, "text": text[:4000],
            "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=10)
    except Exception:
        pass


def main():
    offset = None
    try:
        r = requests.get(TG + "/getUpdates", params={"offset": -1, "timeout": 0}, timeout=10).json()
        res = r.get("result", [])
        if res:
            offset = res[-1]["update_id"] + 1
    except Exception:
        pass
    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset
            r = requests.get(TG + "/getUpdates", params=params, timeout=40).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message") or u.get("edited_message") or {}
                chat = (msg.get("chat") or {}).get("id")
                text = msg.get("text", "")
                if not chat or not text:
                    continue
                if ALLOWED and str(chat) not in ALLOWED:
                    send(chat, "⛔ No autorizado.")
                    continue
                try:
                    send(chat, answer(text))
                except Exception as e:
                    send(chat, "Error consultando datos: " + esc(e))
        except Exception:
            time.sleep(3)


if __name__ == "__main__":
    main()
