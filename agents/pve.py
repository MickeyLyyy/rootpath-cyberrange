import requests, urllib3, config
urllib3.disable_warnings()
BASE = "https://%s:%d/api2/json" % (config.PVE_HOST, config.PVE_PORT)
H = {"Authorization": "PVEAPIToken=%s=%s" % (config.TOKENID, config.SECRET)}
def _get(path):
    return requests.get(BASE + path, headers=H, verify=False, timeout=8)
def _post(path, data=None):
    return requests.post(BASE + path, headers=H, verify=False, timeout=8, data=data or {})
def node_status():
    return _get("/nodes/%s/status" % config.NODE).json()["data"]
def list_guests():
    out = []
    for t in ("lxc", "qemu"):
        r = _get("/nodes/%s/%s" % (config.NODE, t))
        if r.ok:
            out += r.json()["data"]
    return out
def pool_members():
    r = _get("/pools/%s" % config.POOL)
    return r.json()["data"]["members"] if r.ok else []
def stop_guest(vmid, typ="lxc"):
    return _post("/nodes/%s/%s/%d/status/stop" % (config.NODE, typ, vmid))
