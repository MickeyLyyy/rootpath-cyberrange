import os, json, time, socket, subprocess
import state
PIPE = os.path.dirname(os.path.abspath(__file__))
STAGING = os.path.join(PIPE, "staging")
NET = "rp-pipe-test"

def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)
def _wait_port(port, timeout=40):
    end = time.time() + timeout
    while time.time() < end:
        s = socket.socket()
        s.settimeout(1)
        try:
            s.connect(("127.0.0.1", port)); s.close(); return True
        except OSError:
            s.close(); time.sleep(1)
    return False


def _wait_web(port, timeout=60, path="/"):
    end = time.time() + timeout
    while time.time() < end:
        r = _run(["curl","-s","-o","/dev/null","-m","2","-w","%{http_code}",
                  "http://127.0.0.1:%d%s" % (port, path)])
        if r.returncode == 0 and r.stdout.strip() not in ("", "000"):
            return True
        time.sleep(1)
    return False

def _wait_ssh(port, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        try:
            sk = socket.create_connection(("127.0.0.1", port), timeout=2)
            sk.settimeout(3)
            data = sk.recv(64); sk.close()
            if data.startswith(b"SSH-"):
                return True
        except OSError:
            pass
        time.sleep(1)
    return False

def _wait_ready(meta, port):
    t = meta["spec"]["template"]
    if t == "linux_suid":
        return _wait_ssh(port)
    if t.startswith("web_"):
        return _wait_web(port)
    return True

def _negatives(meta, port):
    t = meta["spec"]["template"]; slug = meta["slug"]; flag = meta["flag"]; c = "rp-test-" + slug
    if t == "linux_suid":
        r = _run(["docker","exec",c,"stat","-c","%a","/root/flag.txt"])
        if r.stdout.strip() != "600":
            return "flag no tiene permisos 600 (%s)" % r.stdout.strip()
        r = _run(["docker","exec","--user",meta["neg_help"]["user"],c,"cat","/root/flag.txt"])
        if flag in r.stdout:
            return "flag legible por el usuario sin escalar"
    if t == "web_idor":
        r = _run(["curl","-s","http://127.0.0.1:%d/user/1" % port])
        if flag in r.stdout:
            return "flag accesible sin IDOR"
    if t == "web_cmdi":
        r = _run(["curl","-s","http://127.0.0.1:%d/" % port])
        if flag in r.stdout:
            return "flag expuesta sin inyeccion de comandos"
    if t == "web_lfi":
        r = _run(["curl","-s","http://127.0.0.1:%d/?page=home" % port])
        if flag in r.stdout:
            return "flag expuesta sin traversal"
    if t == "crypto_vigenere":
        raw = open(os.path.join(STAGING, slug, meta["file"])).read()
        if flag in raw:
            return "flag en texto plano en el adjunto"
    return None

def validate(slug):
    d = os.path.join(STAGING, slug)
    mpath = os.path.join(d, "meta.json")
    if not os.path.exists(mpath):
        return {"success": False, "error": "no existe %s" % slug}
    meta = json.load(open(mpath)); flag = meta["flag"]
    logs = []
    if meta["kind"] == "service":
        img = "rp-pipeline-" + slug
        r = _run(["docker","build","-t",img,d]); logs.append("build rc=%d" % r.returncode)
        if r.returncode != 0:
            return {"success": False, "step": "build", "error": r.stderr[-400:]}
        _run(["docker","network","create",NET])
        _run(["docker","rm","-f","rp-test-"+slug])
        port = meta["host_port"]; iport = meta["internal_port"]
        r = _run(["docker","run","-d","--name","rp-test-"+slug,"--network",NET,
                  "-p","%d:%d" % (port, iport), img])
        logs.append("run rc=%d" % r.returncode)
        if r.returncode != 0:
            return {"success": False, "step": "run", "error": r.stderr[-400:]}
        if not _wait_ready(meta, port):
            _run(["docker","rm","-f","rp-test-"+slug])
            return {"success": False, "step": "wait", "error": "puerto no abierto"}
        env = dict(os.environ, PORT=str(port))
        r = _run(["bash", os.path.join(d,"solve.sh")], env=env)
        out = r.stdout + r.stderr
        logs.append("solve rc=%d" % r.returncode)
        if flag not in out:
            dl = _run(["docker","logs","rp-test-"+slug]).stdout
            ps = _run(["docker","ps","-a","--filter","name=rp-test-"+slug]).stdout
            _run(["docker","rm","-f","rp-test-"+slug])
            return {"success": False, "step": "solve", "error": out[-400:], "dockerlogs": dl[-500:], "ps": ps[:300], "port": port}
        n = _negatives(meta, port)
        _run(["docker","rm","-f","rp-test-"+slug])
        if n:
            return {"success": False, "step": "negativo", "error": n}
    else:
        env = dict(os.environ, FILE=os.path.join(d, meta["file"]))
        r = _run(["bash", os.path.join(d,"solve.sh")], env=env)
        out = r.stdout + r.stderr
        logs.append("solve rc=%d" % r.returncode)
        if flag not in out:
            return {"success": False, "step": "solve", "error": out[-400:]}
        n = _negatives(meta, 0)
        if n:
            return {"success": False, "step": "negativo", "error": n}
    state.set_state(slug, "validated", validated=time.time())
    return {"success": True, "slug": slug, "flag": flag, "logs": logs}
