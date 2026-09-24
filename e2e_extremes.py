import re, time, subprocess
import requests

B = "http://127.0.0.1:8000"
ADMIN_PASS = "RP-485403160cbe4f714c19f5ab"
TOK = open("/opt/rootpath/.admin_token").read().strip()
CHALLS = [("BancoQuisqueya - Banca Digital", "/tmp/solve_bq.py"),
          ("LuzClara Telecom - Facturacion Electronica (e-CF)", "/tmp/solve_lc.py"),
          ("EDQ Energia - Portal de Servicios", "/tmp/solve_edq.py")]

s = requests.Session()
n = re.search(r'name="nonce" value="([^"]*)"',
              s.get(B + "/plugins/rootpath/welcome").text).group(1)
s.post(B + "/login", data={"name": "admin", "password": ADMIN_PASS, "nonce": n},
       allow_redirects=True)
csrf = re.search(r'csrf-token"\s+content="([^"]*)"',
                 s.get(B + "/plugins/rootpath/dashboard").text).group(1)
H = {"CSRF-Token": csrf, "Content-Type": "application/json"}
by_name = {c["name"]: c["id"] for c in
           requests.get(B + "/api/v1/challenges?view=admin",
                        headers={"Authorization": "Token " + TOK,
                                 "Content-Type": "application/json"}).json()["data"]}

for name, solver in CHALLS:
    cid = by_name[name]
    r = s.post(B + "/plugins/rootpath/api/lab/control", headers=H,
               json={"name": name, "action": "start"})
    port = r.json().get("host_port")
    print("== %s | cid %s | port %s" % (name, cid, port))
    time.sleep(6)
    p = subprocess.run(["python3", solver, str(port)], capture_output=True, text=True,
                       timeout=120)
    flag = None
    for line in (p.stdout + p.stderr).splitlines():
        m = re.search(r"FLAG: (RP\{[^}]*\})", line)
        if m:
            flag = m.group(1)
    print("  flag:", flag)
    att = s.post(B + "/api/v1/challenges/attempt", headers=H,
                 json={"challenge_id": cid, "submission": flag}).json().get("data")
    print("  submit:", att)
    s.post(B + "/plugins/rootpath/api/lab/control", headers=H,
           json={"name": name, "action": "stop"})
    print("  stop OK")
print("E2E COMPLETO")
