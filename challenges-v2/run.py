# -*- coding: utf-8 -*-
"""Orquestador de challenges-v2: reset, generate, deploy, validate, load."""
import json, os, socket, subprocess, sys, time

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(BASE, "build")
CTFD = "http://127.0.0.1:8000"
HOST = "172.170.10.11"

from specs import SPECS
from tpl_util import gen_flag, render_docs, DIFF_NAME, PTS
from tpl_web import BUILDERS as WEB
from tpl_linux import BUILDERS as LINUX
from tpl_crypto import BUILDERS as CRYPTO
from tpl_forensics import BUILDERS as FORENSICS
from tpl_ad import BUILDERS as AD
from tpl_blue import BUILDERS as BLUE

BUILDERS = {}
for m in (WEB, LINUX, CRYPTO, FORENSICS, AD, BLUE):
    BUILDERS.update(m)


def _token():
    return open("/opt/rootpath/.admin_token").read().strip()


def _agent_key():
    return open("/opt/rootpath/runtime/agent_key").read().strip()


def _H():
    return {"Authorization": "Token " + _token(), "Content-Type": "application/json"}


def flag_for(spec):
    if spec["template"] == "ad_kerberoast":
        return "RP{%s_%s}" % (spec["spec"]["user"], spec["spec"]["password"])
    return gen_flag(spec["slug"])


def description(spec, meta):
    return "\n".join([
        "ROOTPATH // EXPEDIENTE %s" % spec["rd"],
        "",
        "**Tipo de incidente:** %s" % spec["incidente"],
        "**Dificultad:** %s" % DIFF_NAME[spec["difficulty"]],
        "**Provincia:** %s" % spec["provincia"],
        "",
        spec["resumen"],
        "",
        "**Conexión:** %s" % meta["connection"],
    ])


def generate():
    os.makedirs(BUILD, exist_ok=True)
    port_web = 8081
    port_linux = 2201
    services = {}
    manifest = []
    for spec in SPECS:
        flag = flag_for(spec)
        files, solve, meta, note = BUILDERS[spec["template"]](spec, flag)
        slug = spec["slug"]
        d = os.path.join(BUILD, slug)
        os.makedirs(os.path.join(d, "tests"), exist_ok=True)
        if meta["kind"] == "service":
            if spec["category"] == "Linux":
                hp = port_linux; port_linux += 1
            else:
                hp = port_web; port_web += 1
            meta["host_port"] = hp
            services[slug] = {"host_port": hp, "internal_port": meta["internal_port"]}
        else:
            meta["host_port"] = None
        if meta["kind"] == "service":
            if spec["category"] == "Linux":
                meta["connection"] = "ssh %s@%s -p %d (password: %s)" % (meta["user"], HOST, meta["host_port"], meta["password"])
            else:
                meta["connection"] = "http://%s:%d/" % (HOST, meta["host_port"])
        files.update(render_docs(spec, flag, meta, note))
        for path, content in files.items():
            p = os.path.join(d, path)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if isinstance(content, bytes):
                with open(p, "wb") as fh:
                    fh.write(content)
            else:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(content)
        sp = os.path.join(d, "tests", "solve.sh")
        with open(sp, "w") as fh:
            fh.write(solve)
        os.chmod(sp, 0o755)
        meta2 = {"slug": slug, "flag": flag, "kind": meta["kind"],
                 "host_port": meta.get("host_port"), "internal_port": meta.get("internal_port"),
                 "user": meta.get("user"), "password": meta.get("password"),
                 "file": meta.get("file"), "template": spec["template"], "title": spec["title"],
                 "category": spec["category"], "value": PTS[spec["difficulty"]],
                 "cert": spec["cert"], "domain": spec["domain"], "difficulty": spec["difficulty"]}
        with open(os.path.join(d, "meta.json"), "w") as fh:
            json.dump(meta2, fh, indent=2)
        manifest.append(meta2)
    lines = ["name: rootpath-v2", "services:"]
    for slug, s in services.items():
        lines += ["  %s:" % slug,
                  "    build: ./%s" % slug,
                  "    restart: \"no\"",
                  "    ports: [\"%d:%d\"]" % (s["host_port"], s["internal_port"])]
    with open(os.path.join(BUILD, "docker-compose.yml"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(os.path.join(BUILD, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2)
    print("generated %d challenges (services=%d)" % (len(SPECS), len(services)))


def reset():
    s = requests.Session()
    r = s.get(CTFD + "/api/v1/challenges?view=admin", headers=_H())
    chs = r.json().get("data", [])
    for c in chs:
        rr = s.delete(CTFD + "/api/v1/challenges/%d" % c["id"], headers=_H())
        if rr.status_code == 200:
            print("deleted", c["id"], c["name"])
        else:
            print("FAIL delete", c["id"], c["name"], rr.status_code, rr.text[:120])
    for f in ("/opt/rootpath/challenges/docker-compose.yml",
              "/opt/rootpath/pipeline/published-compose.yml"):
        if os.path.exists(f):
            subprocess.run(["docker", "compose", "-f", f, "down"], capture_output=True, text=True)
    print("reset done. challenges remaining:", end=" ")
    r = s.get(CTFD + "/api/v1/challenges?view=admin", headers=_H())
    print(r.json().get("meta", {}).get("count", "?"))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("generate", "all"):
        generate()
    if cmd in ("reset", "all"):
        reset()
    if cmd in ("deploy", "all"):
        from validate import deploy
        deploy()
    if cmd in ("validate", "all"):
        from validate import validate
        validate()
    if cmd in ("load", "all"):
        from load import load
        load()


if __name__ == "__main__":
    main()
