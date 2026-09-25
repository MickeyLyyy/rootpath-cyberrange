import re, time, subprocess
import requests
B = "http://127.0.0.1:8000"
ADMIN_PASS = "RP-485403160cbe4f714c19f5ab"
TOK = open("/opt/rootpath/.admin_token").read().strip()
NAME = "Colmado - Panel de Diagnostico"
UID = 1

s = requests.Session()
n = re.search(r'name="nonce" value="([^"]*)"',
              s.get(B + "/plugins/rootpath/welcome").text).group(1)
s.post(B + "/login", data={"name": "admin", "password": ADMIN_PASS, "nonce": n},
       allow_redirects=True)
csrf = re.search(r'csrf-token"\s+content="([^"]*)"',
                 s.get(B + "/plugins/rootpath/dashboard").text).group(1)
H = {"CSRF-Token": csrf, "Content-Type": "application/json"}
by = {c["name"]: c["id"] for c in
      requests.get(B + "/api/v1/challenges?view=admin",
                   headers={"Authorization": "Token " + TOK,
                            "Content-Type": "application/json"}).json()["data"]}
cid = by[NAME]

r = s.post(B + "/plugins/rootpath/api/lab/control", headers=H,
           json={"name": NAME, "action": "start"})
print("start:", r.status_code, r.json())
print("connection:", (r.json() or {}).get("connection"))
port = (r.json() or {}).get("host_port")
time.sleep(10)

print("== consumo (en vivo) ==")
print(subprocess.run(["docker", "stats", "--no-stream", "--format",
                      "{{.Name}} CPU={{.CPUPerc}} MEM={{.MemUsage}}"],
                     capture_output=True, text=True).stdout)

p = subprocess.run(["python3", "/tmp/solve_machine.py", str(UID)], capture_output=True,
                   text=True, timeout=180)
print(p.stdout, p.stderr)
flag = None
for line in (p.stdout + p.stderr).splitlines():
    m = re.search(r"FLAG: (RP\{[^}]*\})", line)
    if m:
        flag = m.group(1)
print("flag capturada:", flag)
att = s.post(B + "/api/v1/challenges/attempt", headers=H,
             json={"challenge_id": cid, "submission": flag}).json().get("data")
print("submit:", att)

s.post(B + "/plugins/rootpath/api/lab/control", headers=H,
       json={"name": NAME, "action": "stop"})
print("stop OK")
print("== resto de contenedores rp- ==")
print(subprocess.run(["docker", "ps", "-a", "--filter", "name=rp-", "--format",
                      "{{.Names}} {{.Status}}"], capture_output=True, text=True).stdout)
print("E2E MAQUINA COMPLETO")
