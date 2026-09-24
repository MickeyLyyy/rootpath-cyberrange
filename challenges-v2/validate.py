# -*- coding: utf-8 -*-
"""Validación: deploy + solve.sh + chequeos negativos."""
import json, os, socket, subprocess, time

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(BASE, "build")


def _wait_web(port, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-m", "2", "-w", "%{http_code}",
                            "http://127.0.0.1:%d/" % port], capture_output=True, text=True)
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
            data = sk.recv(64)
            sk.close()
            if data.startswith(b"SSH-"):
                return True
        except OSError:
            pass
        time.sleep(1)
    return False


def deploy():
    r = subprocess.run(["docker", "compose", "-f", os.path.join(BUILD, "docker-compose.yml"),
                        "up", "-d", "--build"], capture_output=True, text=True)
    print("deploy rc", r.returncode, (r.stderr or r.stdout)[-500:])
    return r.returncode == 0


def _negative(m):
    slug = m["slug"]; flag = m["flag"]; t = m["template"]
    try:
        if m["kind"] == "service" and m["category"] == "Linux":
            c = "rootpath-v2-%s-1" % slug
            r = subprocess.run(["docker", "exec", c, "stat", "-c", "%a", "/root/flag.txt"],
                               capture_output=True, text=True)
            if r.stdout.strip() != "600":
                return "flag.txt no es 600 (%s)" % r.stdout.strip()
        if t == "web_idor":
            r = subprocess.run(["curl", "-s", "http://127.0.0.1:%d/ticket/1" % m["host_port"]],
                               capture_output=True, text=True)
            if flag in r.stdout:
                return "flag visible sin IDOR"
        if t == "web_sqli":
            r = subprocess.run(["curl", "-s", "http://127.0.0.1:%d/?usuario=admin&clave=x" % m["host_port"]],
                               capture_output=True, text=True)
            if flag in r.stdout:
                return "flag visible sin inyeccion"
        if m["kind"] == "static" and t not in ("forensics_strings", "forensics_meta"):
            artifact = os.path.join(BUILD, slug, "artifacts", m["file"])
            data = open(artifact, "rb").read()
            if flag.encode() in data:
                return "flag en texto plano en el artefacto"
    except Exception as e:
        return "neg error: %s" % e
    return None


def validate():
    manifest = json.load(open(os.path.join(BUILD, "manifest.json")))
    ok_n = 0
    for m in manifest:
        slug = m["slug"]
        solve_path = os.path.join(BUILD, slug, "tests", "solve.sh")
        env = dict(os.environ)
        if m["kind"] == "service":
            if m["category"] == "Linux":
                env.update(PORT=str(m["host_port"]), USER=m["user"], PASSWORD=m["password"])
                ready = _wait_ssh(m["host_port"])
            else:
                env.update(PORT=str(m["host_port"]))
                ready = _wait_web(m["host_port"])
            if not ready:
                print("FAIL %-28s no listo" % slug)
                continue
        else:
            env["FILE"] = os.path.join(BUILD, slug, "artifacts", m["file"])
        try:
            r = subprocess.run(["bash", solve_path], capture_output=True, text=True, env=env, timeout=130)
        except subprocess.TimeoutExpired:
            print("FAIL %-28s timeout" % slug)
            continue
        out = r.stdout + r.stderr
        ok = m["flag"] in out
        neg = _negative(m)
        if ok and not neg:
            ok_n += 1
            print("OK   %-28s" % slug)
        else:
            d = ""
            if not ok:
                d = " flag falta"
            if neg:
                d += " NEG:" + neg
            print("FAIL %-28s%s" % (slug, d))
    print("\nvalidados: %d/%d" % (ok_n, len(manifest)))


if __name__ == "__main__":
    deploy()
    validate()
