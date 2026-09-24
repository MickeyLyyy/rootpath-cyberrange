# -*- coding: utf-8 -*-
"""Carga los 18 retos a CTFd y mapea cert/dominio vía API del plugin.

Idempotente: si un reto con el mismo nombre ya existe, reutiliza su id y
solo asegura el mapeo cert/dominio (no duplica flags/hints/archivos).
"""
import json, os

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(BASE, "build")
CTFD = "http://127.0.0.1:8000"
HOST = "172.170.10.11"

from specs import SPECS
from tpl_util import DIFF_NAME


def _token():
    return open("/opt/rootpath/.admin_token").read().strip()


def _agent_key():
    return open("/opt/rootpath/runtime/agent_key").read().strip()


def _H():
    return {"Authorization": "Token " + _token(), "Content-Type": "application/json"}


def _connection(m):
    if m["kind"] != "service":
        return "Adjunto: %s" % m["file"]
    if m["category"] == "Linux":
        return "ssh %s@%s -p %d (password: %s)" % (m["user"], HOST, m["host_port"], m["password"])
    return "http://%s:%d/" % (HOST, m["host_port"])


def _description(spec, m):
    return "\n".join([
        "ROOTPATH // EXPEDIENTE %s" % spec["rd"],
        "",
        "**Tipo de incidente:** %s" % spec["incidente"],
        "**Dificultad:** %s" % DIFF_NAME[spec["difficulty"]],
        "**Provincia:** %s" % spec["provincia"],
        "",
        spec["resumen"],
        "",
        "**Conexión:** %s" % _connection(m),
    ])


def _existing_by_name(s):
    r = s.get(CTFD + "/api/v1/challenges?view=admin", headers=_H())
    out = {}
    if r.status_code == 200:
        for c in r.json().get("data", []):
            out[c["name"]] = c["id"]
    return out


def load():
    spec_by = {s["slug"]: s for s in SPECS}
    manifest = json.load(open(os.path.join(BUILD, "manifest.json")))
    s = requests.Session()
    by_name = _existing_by_name(s)
    created = 0
    mapped = 0
    for m in manifest:
        spec = spec_by[m["slug"]]
        slug = m["slug"]
        if m["title"] in by_name:
            cid = by_name[m["title"]]
        else:
            payload = {
                "name": m["title"],
                "category": m["category"],
                "description": _description(spec, m),
                "value": m["value"],
                "type": "standard",
                "state": "visible",
            }
            r = s.post(CTFD + "/api/v1/challenges", json=payload, headers=_H())
            if r.status_code != 200:
                print("FAIL create", slug, r.status_code, r.text[:150])
                continue
            cid = r.json()["data"]["id"]
            created += 1
            s.post(CTFD + "/api/v1/flags", json={"challenge_id": cid, "type": "static",
                                                 "content": m["flag"], "data": ""}, headers=_H())
            for i, hint in enumerate([spec["hint1"], spec["hint2"], spec["hint3"]]):
                s.post(CTFD + "/api/v1/hints", json={"challenge_id": cid, "content": hint,
                                                     "cost": [5, 15, 30][i]}, headers=_H())
            if m["kind"] == "static":
                fpath = os.path.join(BUILD, slug, "artifacts", m["file"])
                with open(fpath, "rb") as fh:
                    fr = s.post(CTFD + "/api/v1/files",
                                headers={"Authorization": "Token " + _token()},
                                files={"file": (m["file"], fh)},
                                data={"challenge_id": cid, "type": "challenge"})
                    if fr.status_code != 200:
                        print("FAIL upload", slug, fr.status_code, fr.text[:150])
        # mapear cert/dominio (idempotente)
        mr = s.post(CTFD + "/plugins/rootpath/api/agent/map",
                    headers={"Authorization": "Token " + _token(),
                             "X-Agent-Key": _agent_key(),
                             "Content-Type": "application/json"},
                    json={"challenge_name": m["title"], "domain_name": spec["domain"]})
        if mr.status_code not in (200, 201):
            print("WARN map", slug, mr.status_code, mr.text[:200])
        else:
            mapped += 1
        print("loaded", slug, "->", m["title"])
    r = s.get(CTFD + "/api/v1/challenges?view=admin", headers=_H())
    data = r.json().get("data", []) if r.status_code == 200 else []
    print("total challenges:", len(data), "| created:", created, "| mapped:", mapped)


if __name__ == "__main__":
    load()
