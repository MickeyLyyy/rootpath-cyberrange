import os, json, time, subprocess, requests
import state
PIPE = os.path.dirname(os.path.abspath(__file__))
STAGING = os.path.join(PIPE, "staging")
COMPOSE = os.path.join(PIPE, "published-compose.yml")
SERVICES = os.path.join(PIPE, "published_services.json")
CTFD = "http://127.0.0.1:8000"
HOST = "172.170.10.11"

def _admin_token():
    return open("/opt/rootpath/.admin_token").read().strip()
def _agent_key():
    return open("/opt/rootpath/runtime/agent_key").read().strip()
def _H():
    return {"Authorization": "Token " + _admin_token(), "Content-Type": "application/json"}
def _load_services():
    return json.load(open(SERVICES)) if os.path.exists(SERVICES) else {}
def _save_services(d):
    json.dump(d, open(SERVICES, "w"), indent=2)
def _regen_compose():
    svc = _load_services()
    lines = ["name: rootpath-published", "services:"]
    for slug, s in svc.items():
        lines += ["  %s:" % slug,
                  "    build: %s" % os.path.join(STAGING, slug),
                  "    restart: unless-stopped",
                  "    ports: [\"%d:%d\"]" % (s["host_port"], s["internal_port"])]
    open(COMPOSE, "w").write("\n".join(lines) + "\n")
def _connection(meta):
    spec = meta["spec"]
    if meta["kind"] == "service":
        if spec["template"] == "linux_suid":
            return "ssh %s@%s -p %d (password: %s)" % (
                meta["neg_help"]["user"], HOST, meta["host_port"], meta["neg_help"].get("password", "player"))
        return "http://%s:%d/" % (HOST, meta["host_port"])
    return "Adjunto: %s" % meta["file"]
def _load_ctfd(meta, st):
    name = st["title"]; conn = _connection(meta)
    desc = (meta["spec"].get("description", "") + "\n\nConexion: " + conn).strip()
    r = requests.post(CTFD + "/api/v1/challenges", headers=_H(),
        json={"name": name, "category": st["category"], "description": desc,
              "value": st["value"], "type": "standard", "state": "visible"})
    if r.status_code != 200:
        return {"challenge_id": None, "error": r.text[:200]}
    cid = r.json()["data"]["id"]
    requests.post(CTFD + "/api/v1/flags", headers=_H(),
        json={"challenge_id": cid, "content": meta["flag"], "type": "static", "data": "case_insensitive"})
    for cost, text in [(5, meta["spec"].get("hint1", "Observa la aplicacion.")),
                       (15, meta["spec"].get("hint2", "Aplica la tecnica clasica.")),
                       (30, meta["spec"].get("hint3", "Consulta la solucion de referencia."))]:
        requests.post(CTFD + "/api/v1/hints", headers=_H(),
            json={"challenge_id": cid, "content": text, "cost": cost})
    if meta["kind"] == "static":
        path = os.path.join(STAGING, meta["slug"], meta["file"])
        with open(path, "rb") as fh:
            rr = requests.post(CTFD + "/api/v1/files", headers={"Authorization": "Token " + _admin_token()},
                data={"type": "challenge", "challenge_id": str(cid)}, files={"file": (meta["file"], fh)})
        if rr.status_code == 200:
            loc = rr.json()["data"][0]["location"]
            requests.patch(CTFD + "/api/v1/challenges/%d" % cid, headers=_H(), json={"files": [loc]})
    requests.post(CTFD + "/plugins/rootpath/api/agent/map",
        headers={"Content-Type": "application/json", "X-Agent-Key": _agent_key(), "Authorization": "Token " + _admin_token()},
        json={"challenge_name": name, "domain_name": st.get("domain")})
    return {"challenge_id": cid}
def publish(slug):
    st = state.get(slug)
    if not st:
        return {"success": False, "error": "no existe"}
    if st["state"] not in ("approved", "published"):
        return {"success": False, "error": "requiere aprobacion humana (estado=%s)" % st["state"]}
    meta = json.load(open(os.path.join(STAGING, slug, "meta.json")))
    if meta["kind"] == "service":
        svc = _load_services()
        svc[slug] = {"host_port": meta["host_port"], "internal_port": meta["internal_port"]}
        _save_services(svc); _regen_compose()
        r = subprocess.run(["docker", "compose", "-f", COMPOSE, "up", "-d"], capture_output=True, text=True)
        if r.returncode != 0:
            return {"success": False, "step": "compose", "error": (r.stderr or r.stdout)[-400:]}
    loaded = _load_ctfd(meta, st)
    state.set_state(slug, "published", published=time.time(), challenge_id=loaded.get("challenge_id"))
    return {"success": True, "slug": slug, "loaded": loaded}
