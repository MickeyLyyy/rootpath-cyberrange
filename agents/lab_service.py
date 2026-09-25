#!/usr/bin/env python3
"""Servicio de control de laboratorios RootPath.

Modo por-usuario (efimero):
  * kind "web"/"linux": un contenedor por (reto, usuario) con puerto propio.
  * kind "machine"    : una red privada por usuario con un objetivo + una caja
                        atacante (terminal web ttyd). Objetivo boot2root.
"""
import json, re, subprocess, random, hashlib, hmac
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


def _atk_cname(service, uid):
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "-", "%s-atk-u%s" % (service, uid))
    return ("rp-" + safe)[:63]


def _subnet(uid):
    uid = int(uid)
    return "10.%d.%d.0/24" % (100 + (uid // 256), uid % 256)


def _range_ips(uid):
    uid = int(uid)
    base = "10.%d.%d" % (100 + (uid // 256), uid % 256)
    return base + ".10", base + ".5"


def _range_net(uid):
    return "rp-range-u%s" % uid


def _ttyd_pass(uid, service):
    try:
        secret = open(BASE + "/runtime/flag_secret").read().strip()
    except Exception:
        secret = "rootpath"
    return hmac.new(secret.encode(), ("ttyd:%d:%s" % (int(uid), service)).encode(),
                    hashlib.sha256).hexdigest()[:12]


def _run(args, t=180):
    return subprocess.run(args, capture_output=True, text=True, timeout=t)


def _used_ports():
    r = _run(["docker", "ps", "--format", "{{.Ports}}"])
    used = set()
    for m in re.finditer(r"0\.0\.0\.0:(\d+)->", r.stdout or ""):
        used.add(int(m.group(1)))
    return used


def _pick_port(pref):
    used = _used_ports()
    try:
        pref = int(pref)
    except Exception:
        pref = 0
    if PORT_MIN <= pref <= PORT_MAX and pref not in used:
        return pref
    free = [p for p in range(PORT_MIN, PORT_MAX + 1) if p not in used]
    if not free:
        return None
    return random.SystemRandom().choice(free)


def _state(cname):
    r = _run(["docker", "ps", "-a", "--filter", "name=^/%s$" % cname, "--format", "{{.State}}"])
    lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
    return {"container": cname, "running": any(s == "running" for s in lines), "states": lines}


def _firewall(subnet, add=True):
    """Best-effort: aislar el rango del usuario de la LAN/host."""
    rules = [
        ["DOCKER-USER", "-s", subnet, "-d", "172.170.10.0/24", "-j", "DROP"],
        ["INPUT", "-s", subnet, "-d", "172.170.10.11", "-j", "DROP"],
    ]
    for chain, *spec in rules:
        for op in (("-I", chain, "1") if add else ("-D", chain)):
            try:
                _run(["iptables", "-w"] + list(op) + spec, t=10)
            except Exception:
                pass


def _ipt(*args):
    try:
        return _run(["iptables"] + list(args), t=10)
    except Exception:
        return None


def _ensure_expose():
    """Permite el acceso externo (tailnet/host) a los rangos internos.

    Docker anade reglas 'raw PREROUTING DROP' por contenedor (anti-spoofing),
    que descartan el trafico entrante de fuera del bridge. Hay que aceptar
    por delante (raw PREROUTING pos 1) y permitir el forward en DOCKER-USER.
    """
    for src in ("100.64.0.0/10", "172.170.10.10"):
        base = ["-s", src, "-d", "10.100.0.0/14", "-j", "ACCEPT"]
        r = _ipt("-t", "raw", "-C", "PREROUTING", *base)
        if r is None or r.returncode != 0:
            _ipt("-t", "raw", "-I", "PREROUTING", "1", *base)
    r = _ipt("-C", "DOCKER-USER", "-i", "eth0", "-d", "10.100.0.0/14", "-j", "ACCEPT")
    if r is None or r.returncode != 0:
        _ipt("-I", "DOCKER-USER", "1", "-i", "eth0", "-d", "10.100.0.0/14", "-j", "ACCEPT")


# ---------- laboratorios de servicio unico (web / linux) ----------
def deploy(entry, cname, host_port, flag=None):
    _run(["docker", "rm", "-f", cname])
    args = ["docker", "run", "-d", "--name", cname, "--restart=no",
            "--memory", MEM, "--cpus", CPUS,
            "-p", "%d:%d" % (host_port, entry["internal_port"])]
    if flag:
        args += ["-e", "RP_FLAG=%s" % flag]
    args += [entry["image"]]
    return _run(args)


def destroy(cname):
    return _run(["docker", "rm", "-f", cname])


# ---------- maquinas boot2root (red privada + caja atacante) ----------
def deploy_machine(entry, cname, host_port, uid, flag):
    service = entry["service"]
    net = _range_net(uid)
    subnet = _subnet(uid)
    ip_t, ip_a = _range_ips(uid)
    atk = _atk_cname(service, uid)
    _run(["docker", "rm", "-f", cname])
    _run(["docker", "rm", "-f", atk])
    _run(["docker", "network", "rm", net])
    r = _run(["docker", "network", "create", "--subnet", subnet, net])
    if r.returncode != 0:
        r = _run(["docker", "network", "create", net])
        if r.returncode != 0:
            return r
    _firewall(subnet, add=True)
    r = _run(["docker", "run", "-d", "--name", cname, "--restart=no",
              "--memory", MEM, "--cpus", CPUS,
              "--network", net, "--ip", ip_t,
              "-e", "RP_FLAG=%s" % flag, entry["target_image"]])
    if r.returncode != 0:
        return r
    r = _run(["docker", "run", "-d", "--name", atk, "--restart=no",
              "--memory", MEM, "--cpus", CPUS,
              "--network", net, "--ip", ip_a,
              "-p", "0.0.0.0:%d:7681" % host_port,
              "-e", "TTYD_USER=player", "-e", "TTYD_PASS=%s" % _ttyd_pass(uid, service),
              entry["attacker_image"]])
    _ensure_expose()
    return r


def destroy_machine(entry, cname, uid):
    service = entry["service"]
    atk = _atk_cname(service, uid)
    _run(["docker", "rm", "-f", cname])
    _run(["docker", "rm", "-f", atk])
    _run(["docker", "network", "rm", _range_net(uid)])
    _firewall(_subnet(uid), add=False)


def status_machine(entry, uid):
    cname = _cname(entry["service"], uid)
    atk = _atk_cname(entry["service"], uid)
    s1 = _state(cname)
    s2 = _state(atk)
    ip_t, _ = _range_ips(uid)
    return {"container": cname, "attacker": atk,
            "running": s1["running"] and s2["running"],
            "target_ip": ip_t, "states": s1["states"] + s2["states"]}


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
            if e.get("kind") == "machine":
                st = status_machine(e, uid)
                return self._send(200, {"name": name, "service": e["service"],
                                        "kind": "machine", **st})
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
            port = _pick_port(host_port)
            if not port:
                return self._send(503, {"error": "sin puertos libres"})
            cname = _cname(e["service"], uid)
            if e.get("kind") == "machine":
                r = deploy_machine(e, cname, port, uid, flag)
                if r.returncode != 0:
                    return self._send(200, {"ok": False, "out": (r.stdout + r.stderr)[-300:]})
                ip_t, _ = _range_ips(uid)
                return self._send(200, {"ok": True, "container": cname, "service": e["service"],
                                        "image": e["target_image"], "kind": "machine",
                                        "host_port": port, "target_ip": ip_t,
                                        "ttyd_user": "player",
                                        "ttyd_pass": _ttyd_pass(uid, e["service"])})
            r = deploy(e, cname, port, flag)
            if r.returncode != 0:
                return self._send(200, {"ok": False, "out": (r.stdout + r.stderr)[-300:]})
            return self._send(200, {"ok": True, "container": cname, "service": e["service"],
                                    "image": e["image"], "internal_port": e["internal_port"],
                                    "kind": e.get("kind"), "host_port": port})
        if u.path == "/lab/destroy":
            b = self._body()
            name = b.get("name"); uid = b.get("uid"); cname = b.get("container")
            e = _entry(name)
            if e and e.get("kind") == "machine":
                cname = cname or _cname(e["service"], uid)
                destroy_machine(e, cname, uid)
                return self._send(200, {"ok": True, "container": cname})
            if not cname:
                if not e:
                    return self._send(404, {"error": "no lab", "name": name})
                cname = _cname(e["service"], uid)
            r = destroy(cname)
            return self._send(200, {"ok": True, "container": cname,
                                    "out": (r.stdout + r.stderr)[-200:]})
        if u.path.startswith("/lab/"):
            return self._send(404, {"error": "accion no soportada"})
        return self._send(404, {"error": "not found"})


if __name__ == "__main__":
    _ensure_expose()
    HTTPServer(("0.0.0.0", 9001), H).serve_forever()
