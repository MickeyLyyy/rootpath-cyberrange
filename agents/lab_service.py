#!/usr/bin/env python3
"""Servicio de control de laboratorios (start/stop/restart) con allowlist y clave."""
import json, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

BASE = "/opt/rootpath"
KEY = open(BASE + "/runtime/agent_key").read().strip()
MAP = json.load(open(BASE + "/runtime/lab_map.json"))
FILES = {
  "challenges": BASE + "/challenges/docker-compose.yml",
  "platform":   BASE + "/docker-compose.yml",
  "published":  BASE + "/pipeline/published-compose.yml",
}

def state(entry):
    r = subprocess.run(["docker", "ps", "-a", "--filter", "name=%s" % entry["service"],
                        "--format", "{{.State}}"], capture_output=True, text=True)
    lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
    return {"running": any(s == "running" for s in lines), "states": lines}

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
    def do_GET(self):
        if not self._auth():
            return self._send(403, {"error": "forbidden"})
        u = urlparse(self.path)
        if u.path == "/lab/status":
            name = parse_qs(u.query).get("name", [""])[0]
            e = MAP.get(name)
            if not e:
                return self._send(404, {"error": "no lab", "name": name})
            st = state(e)
            return self._send(200, {"name": name, "service": e["service"], "file": e["file"], **st})
        return self._send(404, {"error": "not found"})
    def do_POST(self):
        if not self._auth():
            return self._send(403, {"error": "forbidden"})
        u = urlparse(self.path)
        if u.path.startswith("/lab/"):
            action = u.path.rsplit("/", 1)[-1]
            if action not in ("start", "stop", "restart"):
                return self._send(400, {"error": "bad action"})
            n = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            name = body.get("name")
            e = MAP.get(name)
            if not e:
                return self._send(404, {"error": "no lab", "name": name})
            r = subprocess.run(["docker", "compose", "-f", FILES[e["file"]], action, e["service"]],
                               capture_output=True, text=True, timeout=180)
            return self._send(200, {"ok": r.returncode == 0, "action": action,
                                    "service": e["service"], "out": (r.stdout + r.stderr)[-200:]})
        return self._send(404, {"error": "not found"})

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 9001), H).serve_forever()
