# -*- coding: utf-8 -*-
"""rootpath_exporter - metricas propias del cyber range en formato Prometheus."""
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import pymysql

DBHOST = os.environ.get("DB_HOST", "rootpath-platform-db-1")
DBPORT = int(os.environ.get("DB_PORT", "3306"))
DBUSER = os.environ.get("DB_USER", "root")
DBPASS = os.environ.get("DB_PASS", "")
DBNAME = os.environ.get("DB_NAME", "ctfd")
PORT = int(os.environ.get("PORT", "9200"))


def query(sql):
    con = pymysql.connect(host=DBHOST, port=DBPORT, user=DBUSER, password=DBPASS,
                          database=DBNAME, connect_timeout=5, read_timeout=8)
    try:
        with con.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        con.close()


def esc(v):
    return str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def block(name, mtype, help_, samples):
    out = ["# HELP %s %s" % (name, help_), "# TYPE %s %s" % (name, mtype)]
    for labels, val in samples:
        out.append("%s{%s} %s" % (name, labels, val) if labels else "%s %s" % (name, val))
    return out


def collect():
    lines = []
    errors = []

    def one(fn):
        try:
            lines.extend(fn())
        except Exception as e:
            errors.append(str(e))

    one(lambda: block("rootpath_instances_active", "gauge", "Instancias de laboratorio activas",
                      [("", query("SELECT COUNT(*) FROM rp_lab_instances")[0][0])]))
    one(lambda: block("rootpath_instances_by_kind", "gauge", "Instancias por tipo",
                      [('kind="%s"' % esc(k), v) for k, v in
                       query("SELECT COALESCE(kind,'?'), COUNT(*) FROM rp_lab_instances GROUP BY kind")]))
    one(lambda: block("rootpath_ports_used", "gauge", "Puertos de laboratorio asignados",
                      [("", query("SELECT COUNT(*) FROM rp_lab_instances WHERE host_port IS NOT NULL")[0][0])]))
    one(lambda: block("rootpath_deploys_total", "counter",
                      "Acciones de laboratorio por accion y resultado",
                      [('action="%s",result="%s"' % (esc(a), esc(r)), c) for a, r, c in
                       query("SELECT COALESCE(action,'?'), COALESCE(result,'?'), COUNT(*) "
                             "FROM rp_lab_actions GROUP BY action, result")]))
    one(lambda: block("rootpath_users_total", "gauge", "Usuarios registrados",
                      [("", query("SELECT COUNT(*) FROM users")[0][0])]))
    one(lambda: block("rootpath_solves_total", "counter", "Resoluciones totales",
                      [("", query("SELECT COUNT(*) FROM solves")[0][0])]))
    one(lambda: block("rootpath_submissions_total", "counter", "Submissions por resultado",
                      [('type="%s"' % esc(t), c) for t, c in
                       query("SELECT COALESCE(type,'?'), COUNT(*) FROM submissions GROUP BY type")]))
    one(lambda: block("rootpath_hint_unlocks_total", "counter", "Pistas desbloqueadas",
                      [("", query("SELECT COUNT(*) FROM unlocks")[0][0])]))
    one(lambda: block("rootpath_challenges_total", "gauge", "Retos por estado",
                      [('state="%s"' % esc(s), c) for s, c in
                       query("SELECT COALESCE(state,'?'), COUNT(*) FROM challenges GROUP BY state")]))
    lines += block("rootpath_up", "gauge", "Exporter operativo", [("", 0 if errors else 1)])
    if errors:
        lines.append('# rootpath_exporter_error "%s"' % esc("; ".join(errors)[:400]))
    return "\n".join(lines) + "\n"


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/metrics"):
            body = collect().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"rootpath_exporter ok\n")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
