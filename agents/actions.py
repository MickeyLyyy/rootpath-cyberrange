import json, os, sys, config, pve, requests
sys.path.append("/opt/rootpath/pipeline")

def _rt(name, default=None):
    p = os.path.join(config.RUNTIME, name)
    return open(p).read().strip() if os.path.exists(p) else default
def _write_rt(name, content):
    os.makedirs(config.RUNTIME, exist_ok=True)
    open(os.path.join(config.RUNTIME, name), "w").write(content)
def _ctfd(path, token=None, extra=None):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Token " + token
    if extra:
        h.update(extra)
    r = requests.get(config.CTFD_BASE + path, headers=h, timeout=8)
    return r.json()

def execute(action, params):
    if action == "read_metrics":
        s = pve.node_status(); m = s["memory"]
        return {"cpu_pct": round(s["cpu"] * 100, 1),
                "mem_pct": round(m["used"] / m["total"] * 100, 1),
                "loadavg": s.get("loadavg"), "uptime": s.get("uptime")}
    if action == "list_guests":
        return pve.list_guests()
    if action == "pool_members":
        return pve.pool_members()
    if action == "stop_guest":
        vmid = int(params["vmid"]); typ = params.get("type", "lxc")
        members = pve.pool_members()
        if not any(m.get("vmid") == vmid for m in members):
            raise PermissionError("guest %d no pertenece al pool %s" % (vmid, config.POOL))
        r = pve.stop_guest(vmid, typ)
        return {"vmid": vmid, "type": typ, "http": r.status_code}
    if action == "set_deploy_paused":
        v = bool(params.get("paused"))
        _write_rt("deploy_paused", "1" if v else "0")
        return {"deploy_paused": v}
    if action == "write_status":
        _write_rt("monitor_status.json", json.dumps(params.get("status", {}), indent=2))
        return {"ok": True}
    if action == "alert":
        return {"alert": params}
    if action == "list_paths":
        return _ctfd("/plugins/rootpath/api/paths", token=params.get("token"))
    if action == "recommend_next":
        data = _ctfd("/plugins/rootpath/api/paths", token=params.get("token"))
        cert_id = params.get("cert_id")
        best = None
        for c in data.get("data", []):
            if cert_id and c.get("id") != int(cert_id):
                continue
            for d in c.get("domain_detail", []):
                for ch in d["challenges"]:
                    if not ch["solved"] and (best is None or ch["value"] < best["value"]):
                        best = {"challenge_id": ch["id"], "name": ch["name"], "value": ch["value"],
                                "category": ch["category"], "cert": c["name"], "domain": d["name"]}
        return {"recommendation": best}
    if action == "request_deploy":
        return {"requested": params, "note": "Fase 3: registro/recomendacion; aprovisionamiento = Fase 1"}
    if action == "get_hint":
        key = _rt("agent_key", "")
        cid = int(params["challenge_id"]); level = int(params.get("level", 1))
        return _ctfd("/plugins/rootpath/api/agent/hint?challenge_id=%d&level=%d" % (cid, level),
                     extra={"X-Agent-Key": key})
    if action == "generate_challenge":
        import generator
        return generator.generate(params)
    if action == "list_staging":
        import state as _st
        return _st.load()
    if action == "validate_challenge":
        import validator
        return validator.validate(params["slug"])
    if action == "approve_challenge":
        import state as _st
        return _st.set_state(params["slug"], "approved", approved_by=params.get("by", "mentor"))
    if action == "publish_challenge":
        import publisher
        return publisher.publish(params["slug"])
    if action == "read_flag":
        raise PermissionError("accion prohibida para todos los agentes")
    raise ValueError("accion desconocida: " + action)
