import os, sys, json, base64, secrets, subprocess, requests
sys.path.insert(0, "/opt/rootpath/expansion")
import crypto_helpers as ch

BASE = "/opt/rootpath/expansion/challenges"
CTFD = "http://127.0.0.1:8000"
TOK = open("/opt/rootpath/.admin_token").read().strip()
H = {"Authorization": "Token " + TOK, "Content-Type": "application/json"}
WORDS = ["password","backup2023","Summer2023!","P@ssw0rd","rootpath2024","Winter2024!","svcpass"]

def rand(slug): return "RP{%s_%s}" % (slug.replace("-","_"), secrets.token_hex(3))

def write(slug, files):
    d = os.path.join(BASE, slug); os.makedirs(d, exist_ok=True)
    for name, content in files.items():
        p = os.path.join(d, name)
        if name in ("solve.sh",):
            open(p, "w").write(content); os.chmod(p, 0o755)
        else:
            open(p, "wb").write(content if isinstance(content, bytes) else content.encode())
    return d

def solve_sh(slug, body):
    return "#!/usr/bin/env bash\n" + body

CHALLENGES = []

# ---- AD: enumeracion LDAP (anon) ----
flag = rand("ad-ldap-enum")
ldif = (
 "dn: cn=admin,dc=rootpath,dc=local\ncn: admin\n\n"
 "dn: cn=svc_backup,cn=Users,dc=rootpath,dc=local\ncn: svc_backup\nsAMAccountName: svc_backup\ndescription:: %s\n\n"
 "dn: cn=j.smith,cn=Users,dc=rootpath,dc=local\ncn: j.smith\ndescription: usuario estandar\n\n"
) % base64.b64encode(flag.encode()).decode()
solve = solve_sh("ad-ldap-enum", '''
python3 - "$FILE" <<'PY'
import sys, base64, re
s = open(sys.argv[1], errors="ignore").read()
for m in re.finditer(r"^description:: (.+)$", s, re.M):
    try:
        d = base64.b64decode(m.group(1)).decode(errors="ignore")
        if "RP{" in d: print(d.strip())
    except Exception: pass
PY
''')
CHALLENGES.append(dict(slug="ad-ldap-enum", title="Enumeracion LDAP anonima", category="AD", value=100,
  cert="Pentesting de Active Directory (PNPT)", domain="Enumeracion de Active Directory", difficulty=2,
  desc="Volcado de un directorio (LDIF). El enlace anonimo permite leer atributos: encuentra la flag en la descripcion codificada.",
  h1="Busca atributos description (base64 se marca con ::).",
  h2="description:: almacena base64.", h3="Decodifica el base64 del description de svc_backup.",
  files={"ldap_dump.ldif": ldif}, solve=solve, flag=flag, plaintext_absent=True,
  negative=lambda d: flag in open(os.path.join(d,"ldap_dump.ldif")).read()))

# ---- AD: BloodHound ----
flag = rand("ad-bloodhound")
nodes = {
  "users":[
    {"name":"ADMINISTRATOR@ROOTPATH.LOCAL","properties":{"admincount":1}},
    {"name":"HELPDESK@ROOTPATH.LOCAL","properties":{"description":base64.b64encode(b"cuenta de soporte").decode()}},
    {"name":"J.SMITH@ROOTPATH.LOCAL","properties":{"description":base64.b64encode(flag.encode()).decode()}},
    {"name":"SVC_BACKUP@ROOTPATH.LOCAL","properties":{"description":base64.b64encode(b"servicio de backups").decode()}},
  ],
  "groups":[{"name":"DOMAIN ADMINS@ROOTPATH.LOCAL"},{"name":"DOMAIN CONTROLLERS@ROOTPATH.LOCAL"}],
  "computers":[{"name":"DC01.ROOTPATH.LOCAL"}],
  "edges":[{"source":"J.SMITH@ROOTPATH.LOCAL","target":"DOMAIN CONTROLLERS@ROOTPATH.LOCAL","label":"AdminTo"},
           {"source":"HELPDESK@ROOTPATH.LOCAL","target":"J.SMITH@ROOTPATH.LOCAL","label":"GenericAll"}]
}
solve = solve_sh("ad-bloodhound", '''
python3 - "$FILE" <<'PY'
import sys, json, base64
d = json.load(open(sys.argv[1]))
for e in d.get("edges", []):
    if e.get("label") == "AdminTo" and "DOMAIN CONTROLLERS" in e.get("target",""):
        for u in d["users"]:
            if u["name"] == e["source"]:
                print(base64.b64decode(u["properties"]["description"]).decode())
PY
''')
CHALLENGES.append(dict(slug="ad-bloodhound", title="Ruta a Domain Admin", category="AD", value=150,
  cert="Pentesting de Active Directory (PNPT)", domain="Enumeracion de Active Directory", difficulty=2,
  desc="Export de BloodHound (grafo JSON). Encuentra el usuario con AdminTo sobre Domain Controllers; su description (base64) es la flag.",
  h1="Recorre los edges buscando AdminTo.", h2="El target es DOMAIN CONTROLLERS.",
  h3="La flag esta en base64 en la description de ese usuario.",
  files={"bloodhound.json": json.dumps(nodes, indent=2)}, solve=solve, flag=flag, plaintext_absent=True,
  negative=lambda d: flag in open(os.path.join(d,"bloodhound.json")).read()))

# ---- AD: Kerberoasting ----
pw = "Summer2023!"
flag = "RP{svc_backup_%s}" % pw
kh = ch.kerb_hash(pw, "svc_backup", "ROOTPATH.LOCAL", "MSSQLSvc/db01.rootpath.local:1433")
solve = solve_sh("ad-kerberoast", 'python3 /opt/rootpath/expansion/cracker.py "$FILE" svc_backup\n')
CHALLENGES.append(dict(slug="ad-kerberoast", title="Kerberoasting", category="AD", value=200,
  cert="Pentesting de Active Directory (PNPT)", domain="Ataques a credenciales", difficulty=3,
  desc="Hash TGS-REP (etype 23) del servicio svc_backup. Crackea la contrasena con wordlist y obtiene la flag RP{usuario_password}.",
  h1="Es un hash $krb5tgs$23$ (Kerberoast).", h2="Crackea RC4-HMAC con un diccionario.",
  h3="La contrasena esta en un diccionario pequeno de servicios.",
  files={"kerberoast.txt": kh + "\n"}, solve=solve, flag=flag, plaintext_absent=True,
  negative=lambda d: pw in open(os.path.join(d,"kerberoast.txt")).read()))

# ---- AD: AS-REP Roasting ----
pw = "Winter2024!"
flag = "RP{nopreauth_%s}" % pw
ah = ch.asrep_hash(pw, "nopreauth", "ROOTPATH.LOCAL")
solve = solve_sh("ad-asrep", 'python3 /opt/rootpath/expansion/cracker.py "$FILE" nopreauth\n')
CHALLENGES.append(dict(slug="ad-asrep", title="AS-REP Roasting", category="AD", value=200,
  cert="Pentesting de Active Directory (PNPT)", domain="Ataques a credenciales", difficulty=3,
  desc="Hash AS-REP de un usuario sin preautenticacion. Crackea la contrasena y obtiene la flag.",
  h1="Es un hash $krb5asrep$23$ (AS-REP roast).", h2="Crackea RC4-HMAC con diccionario.",
  h3="Usuario sin preauth: nopreauth.",
  files={"asrep.txt": ah + "\n"}, solve=solve, flag=flag, plaintext_absent=True,
  negative=lambda d: pw in open(os.path.join(d,"asrep.txt")).read()))

# ---- AD: reutilizacion de credenciales ----
reuse_user, reuse_pw = "administrator", "rootpath2024"
flag = "RP{%s_%s}" % (reuse_user, reuse_pw)
lines = []
for u in ["svc_backup","helpdesk","j.smith", reuse_user]:
    if u == reuse_user:
        hh = ch.nt_hash(reuse_pw).hex()
    else:
        hh = ch.nt_hash(secrets.token_hex(8)).hex()
    lines.append("%s:%s" % (u, hh))
solve = solve_sh("ad-cred-reuse", '''
python3 - "$FILE" <<'PY'
import sys
sys.path.insert(0, "/opt/rootpath/expansion")
from crypto_helpers import nt_hash
words = ["password","backup2023","Summer2023!","P@ssw0rd","rootpath2024","Winter2024!","svcpass"]
for line in open(sys.argv[1]):
    if ":" not in line: continue
    user, hb = line.strip().split(":", 1)
    for w in words:
        if nt_hash(w).hex() == hb:
            print("RP{%s_%s}" % (user, w)); sys.exit(0)
PY
''')
CHALLENGES.append(dict(slug="ad-cred-reuse", title="Reutilizacion de credenciales", category="AD", value=150,
  cert="Pentesting de Active Directory (PNPT)", domain="Movimiento lateral", difficulty=3,
  desc="Volcado de hashes NTLM. Una cuenta reutiliza una contrasena debil: crackeala y obtiene la flag RP{usuario_password}.",
  h1="Son hashes NTLM (MD4).", h2="Crackea con un diccionario pequeno.",
  h3="Una de las cuentas usa una contrasena reutilizada de servicio.",
  files={"ntlm_hashes.txt": "\n".join(lines) + "\n"}, solve=solve, flag=flag, plaintext_absent=True,
  negative=lambda d: reuse_pw in open(os.path.join(d,"ntlm_hashes.txt")).read()))

# ---- BLUE: web log ----
flag = rand("blue-web-log")
enc = base64.b64encode(flag.encode()).decode()
log = (
 '203.0.113.10 - - [10/Aug/2026:03:14:01 +0000] "GET /index.php HTTP/1.1" 200 1043\n'
 '203.0.113.10 - - [10/Aug/2026:03:14:02 +0000] "GET /login.php HTTP/1.1" 200 812\n'
 '198.51.100.77 - - [10/Aug/2026:03:15:10 +0000] "GET /admin HTTP/1.1" 403 153\n'
 '198.51.100.77 - - [10/Aug/2026:03:15:44 +0000] "POST /api/export?data=%s HTTP/1.1" 200 88\n'
 '203.0.113.10 - - [10/Aug/2026:03:16:00 +0000] "GET /index.php HTTP/1.1" 200 1043\n'
) % enc
solve = solve_sh("blue-web-log", '''
python3 - "$FILE" <<'PY'
import sys, re, base64
for m in re.finditer(r"data=([A-Za-z0-9+/=]+)", open(sys.argv[1]).read()):
    try:
        d = base64.b64decode(m.group(1)).decode()
        if "RP{" in d: print(d)
    except Exception: pass
PY
''')
CHALLENGES.append(dict(slug="blue-web-log", title="Exfiltracion en logs web", category="Blue", value=100,
  cert="Blue Team (BTL1)", domain="Analisis de logs", difficulty=2,
  desc="Log de acceso Apache. Un atacante exfiltro datos en una peticion. Decodifica el parametro y recupera la flag.",
  h1="Hay una peticion POST a /api/export.", h2="El parametro data esta en base64.",
  h3="Decodifica el valor de data.",
  files={"access.log": log}, solve=solve, flag=flag, plaintext_absent=True,
  negative=lambda d: flag in open(os.path.join(d,"access.log")).read()))

# ---- BLUE: auth.log ----
flag = rand("blue-auth")
enc = base64.b64encode(flag.encode()).decode()
lines = []
for i in range(6):
    lines.append('Aug 10 03:0%d:1%d server sshd[%d]: Failed password for invalid user admin from 203.0.113.66 port %d ssh2' % (i, i, 1000+i, 40000+i))
lines.append('Aug 10 03:02:10 server sshd[1100]: Accepted password for webadmin from 203.0.113.66 port 44444 ssh2')
lines.append('Aug 10 03:02:44 server sudo: webadmin : TTY=pts/0 ; PWD=/var/www ; USER=root ; COMMAND=/bin/bash -c "echo %s > /tmp/.cache"' % enc)
lines.append('Aug 10 03:03:01 server sshd[1100]: pam_unix(sshd:session): session closed for user webadmin')
authlog = "\n".join(lines) + "\n"
solve = solve_sh("blue-auth", '''
python3 - "$FILE" <<'PY'
import sys, re, base64
for line in open(sys.argv[1]):
    for m in re.finditer(r"echo ([A-Za-z0-9+/=]+) >", line):
        print(base64.b64decode(m.group(1)).decode())
PY
''')
CHALLENGES.append(dict(slug="blue-auth-bruteforce", title="Fuerza bruta y persistencia", category="Blue", value=150,
  cert="Blue Team (BTL1)", domain="Analisis de logs", difficulty=2,
  desc="auth.log con un ataque de fuerza bruta y acceso exitoso. Tras el acceso, el atacante ejecuto un comando con datos codificados: recupera la flag.",
  h1="Fuerza bruta desde 203.0.113.66, exito con webadmin.",
  h2="Revisa las lineas sudo de webadmin.",
  h3="El comando incluye un valor en base64 tras 'echo'.",
  files={"auth.log": authlog}, solve=solve, flag=flag, plaintext_absent=True,
  negative=lambda d: flag in open(os.path.join(d,"auth.log")).read()))

# ---- BLUE: DNS exfil ----
flag = rand("blue-dns")
b = base64.b32encode(flag.encode()).decode().rstrip("=").lower()
chunks = [b[i:i+16] for i in range(0, len(b), 16)]
dns = ["# Zeek dns.log (columnas: ts id orig query)"] + [
    "%.3f\tC1\t203.0.113.66\t%s.exfil.rootpath.local" % (1.0 + i, c) for i, c in enumerate(chunks)
]
dnslog = "\n".join(dns) + "\n"
solve = solve_sh("blue-dns-exfil", '''
python3 - "$FILE" <<'PY'
import sys, re, base64
labels = []
for line in open(sys.argv[1]):
    m = re.search(r"\t([a-z2-7]+)\.exfil\.rootpath\.local", line)
    if m: labels.append(m.group(1))
data = "".join(labels).upper()
pad = "=" * ((8 - len(data) % 8) % 8)
try:
    print(base64.b32decode(data + pad).decode())
except Exception:
    print(base64.b32decode(data).decode())
PY
''')
CHALLENGES.append(dict(slug="blue-dns-exfil", title="Exfiltracion por DNS", category="Blue", value=200,
  cert="Blue Team (BTL1)", domain="Forense de red", difficulty=3,
  desc="Log DNS (formato Zeek) con exfiltracion de datos en subdominios. Reensambla los labels y decodifica (base32) para obtener la flag.",
  h1="Cada query lleva un trozo de datos en el subdominio.", h2="El esquema de codificacion es base32.",
  h3="Une los labels (sin .exfil...) en orden y decodifica base32.",
  files={"dns.log": dnslog}, solve=solve, flag=flag, plaintext_absent=True,
  negative=lambda d: flag in open(os.path.join(d,"dns.log")).read()))

# ---- validar + cargar ----
def validate(c):
    d = write(c["slug"], c["files"])
    solve_path = os.path.join(d, "solve.sh")
    open(solve_path, "w").write(c["solve"]); os.chmod(solve_path, 0o755)
    artifact = os.path.join(d, list(c["files"].keys())[0])
    env = dict(os.environ, FILE=artifact)
    r = subprocess.run(["bash", solve_path], capture_output=True, text=True, env=env, cwd=d)
    out = r.stdout + r.stderr
    if c["flag"] not in out:
        return False, "solve no obtuvo la flag: " + out[-300:]
    if c.get("plaintext_absent") and c["negative"](d):
        return False, "flag en texto plano en el artefacto"
    return True, "ok"

def load(c):
    r = requests.post(CTFD + "/api/v1/challenges", headers=H,
        json={"name": c["title"], "category": c["category"], "description": c["desc"],
              "value": c["value"], "type": "standard", "state": "visible"})
    if r.status_code != 200:
        return {"error": r.text[:200]}
    cid = r.json()["data"]["id"]
    requests.post(CTFD + "/api/v1/flags", headers=H,
        json={"challenge_id": cid, "content": c["flag"], "type": "static", "data": "case_insensitive"})
    for cost, text in [(5, c["h1"]), (15, c["h2"]), (30, c["h3"])]:
        requests.post(CTFD + "/api/v1/hints", headers=H,
            json={"challenge_id": cid, "content": text, "cost": cost})
    fname = list(c["files"].keys())[0]
    with open(os.path.join(BASE, c["slug"], fname), "rb") as fh:
        rr = requests.post(CTFD + "/api/v1/files", headers={"Authorization": "Token " + TOK},
            data={"type": "challenge", "challenge_id": str(cid)}, files={"file": (fname, fh)})
    if rr.status_code == 200:
        loc = rr.json()["data"][0]["location"]
        requests.patch(CTFD + "/api/v1/challenges/%d" % cid, headers=H, json={"files": [loc]})
    return {"challenge_id": cid}

results = []
for c in CHALLENGES:
    ok, msg = validate(c)
    if not ok:
        print("VALIDATE FAIL %s: %s" % (c["slug"], msg)); results.append((c["slug"], False, msg)); continue
    info = load(c)
    results.append((c["slug"], True, info))
    print("OK %-22s cid=%s" % (c["slug"], info.get("challenge_id")))

print("\nRESUMEN:")
for s, ok, info in results:
    print("  %-22s %s %s" % (s, "OK" if ok else "FAIL", info if not ok else info))
open("/opt/rootpath/expansion/loaded.json", "w").write(json.dumps(
    [{"slug": c["slug"], "title": c["title"], "cert": c["cert"], "domain": c["domain"]} for c in CHALLENGES], indent=2))
