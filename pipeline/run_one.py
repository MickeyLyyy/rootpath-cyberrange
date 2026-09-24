import sys, json
sys.path.insert(0, "/opt/rootpath/agents")
import bus
spec = {"title":"Auditoria SUID", "template":"linux_suid", "category":"Linux", "value":200,
  "cert":"Fundamentos de Pentesting (eJPT)", "domain":"Explotacion de Sistemas Linux", "difficulty":2,
  "user":"auditor", "password":"auditor", "bin":"sysaudit",
  "description":"Acceso SSH a una caja de auditoria. Encuentra el binario con bit SUID y usalo para leer la flag de root.",
  "hint1":"Busca binarios con bit SUID: find / -perm -4000 -type f 2>/dev/null",
  "hint2":"El binario legado /usr/local/bin/sysaudit se ejecuta como root.",
  "hint3":"Ejecutalo directamente: /usr/local/bin/sysaudit"}
g = bus.call("creador", "generate_challenge", spec)
v = bus.call("validador", "validate_challenge", {"slug": g["slug"]})
print("validado=%s" % v.get("success"))
if v.get("success"):
    bus.call("mentor", "approve_challenge", {"slug": g["slug"], "by": "mentor"})
    p = bus.call("mentor", "publish_challenge", {"slug": g["slug"]})
    print("publicado=%s cid=%s" % (p.get("success"), (p.get("loaded") or {}).get("challenge_id")))
else:
    print(json.dumps(v)[:400])
