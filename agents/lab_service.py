#!/usr/bin/env python3
"""Servicio de control de laboratorios RootPath.

Modo por-usuario (efimero): 'deploy' crea un contenedor nuevo por (reto, usuario)
con puerto propio; 'destroy' lo elimina. Allowlist por name en lab_map.json.
"""
import json, re, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

BASE = "/opt/rootpath"
KEY = open(BASE + "/runtime/agent_key").read().strip()
MAP = json.load(open(BASE + "/runtime/lab_map.json"))

MEM = "256m"
CPUS = "0.5"
PORT_MIN = 30000
PORT_MAX = 40000


def _entry(name):
    return MAP.get(name)


def _cname(service, uid):
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "-", "%s-u%s" % (service, uid))
    return ("rp-" + safe)[:63]


def _run(args, t=180):
    return subprocess.run(args, capture_output=True, text=True, timeout=t)


def _state(cname):
    r = _run(["docker", "ps", "-a", "--filter", "name=^/%s$" % cname, "--format", "{{.State}}"])
    lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
    return {"container": cname, "running": any(s == "running" for s in lines), "states": lines}


def deploy(entry, cname, host_port, flag=None):
    _run(["docker", "rm", "-f", cname])  # limpia restos
    args = ["docker", "run", "-d", "--name", cname, "--restart=no",
            "--memory", MEM, "--cpus", CPUS,
            "-p", "%d:%d" % (host_port, entry["internal_port"])]
    if flag:
        args += ["-e", "RP_FLAG=%s" % flag]
    args += [entry["image"]]
    return _run(args)


def destroy(cname):
    return _run(["docker", "rm", "-f", cname])


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, *a):
        pass

    def _auth(self):
        return self.headers.get("X-Agent-Key", "") == KEY

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if not self._auth():
            return self._send(403, {"error": "forbidden"})
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/lab/status":
            name = q.get("name", [""])[0]
            uid = q.get("uid", [""])[0]
            e = _entry(name)
            if not e:
                return self._send(404, {"error": "no lab", "name": name})
            cname = _cname(e["service"], uid)
            st = _state(cname)
            return self._send(200, {"name": name, "service": e["service"], "image": e["image"],
                                    "internal_port": e["internal_port"], "kind": e.get("kind"),
                                    **st})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth():
            return self._send(403, {"error": "forbidden"})
        u = urlparse(self.path)
        if u.path == "/lab/deploy":
            b = self._body()
            name = b.get("name"); uid = b.get("uid"); host_port = b.get("host_port")
            flag = b.get("flag")
            e = _entry(name)
            if not e:
                return self._send(404, {"error": "no lab", "name": name})
            try:
                host_port = int(host_port)
            except Exception:
                return self._send(400, {"error": "host_port invalido"})
            if not (PORT_MIN <= host_port <= PORT_MAX):
                return self._send(400, {"error": "host_port fuera de rango"})
            cname = _cname(e["service"], uid)
            r = deploy(e, cname, host_port, flag)
            if r.returncode != 0:
                return self._send(200, {"ok": False, "out": (r.stdout + r.stderr)[-300:]})
            return self._send(200, {"ok": True, "container": cname, "service": e["service"],
                                    "image": e["image"], "internal_port": e["internal_port"],
                                    "kind": e.get("kind"), "host_port": host_port})
        if u.path == "/lab/destroy":
            b = self._body()
            name = b.get("name"); uid = b.get("uid"); cname = b.get("container")
            if not cname:
                e = _entry(name)
                if not e:
                    return self._send(404, {"error": "no lab", "name": name})
                cname = _cname(e["service"], uid)
            r = destroy(cname)
            return self._send(200, {"ok": True, "container": cname, "out": (r.stdout + r.stderr)[-200:]})
        if u.path.startswith("/lab/"):
            return self._send(404, {"error": "accion no soportada"})
        return self._send(404, {"error": "not found"})


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 9001), H).serve_forever()
