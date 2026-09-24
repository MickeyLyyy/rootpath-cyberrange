import sys, json
sys.path.insert(0, "/opt/rootpath/agents")
sys.path.insert(0, "/opt/rootpath/pipeline")
import bus, state as st

SPECS = [
 {"title":"Auditoria SUID", "template":"linux_suid", "category":"Linux", "value":200,
  "cert":"Fundamentos de Pentesting (eJPT)", "domain":"Explotacion de Sistemas Linux", "difficulty":2,
  "user":"auditor", "password":"auditor", "bin":"sysaudit",
  "description":"Acceso SSH a una caja de auditoria. Encuentra el binario con bit SUID y usalo para leer la flag de root.",
  "hint1":"Busca binarios con bit SUID: find / -perm -4000 -type f 2>/dev/null",
  "hint2":"El binario legado /usr/local/bin/sysaudit se ejecuta como root.",
  "hint3":"Ejecutalo directamente: /usr/local/bin/sysaudit"},
 {"title":"Panel de Perfiles", "template":"web_idor", "category":"Web", "value":100,
  "cert":"Fundamentos de Pentesting (eJPT)", "domain":"Reconocimiento y Web", "difficulty":2,
  "description":"API de perfiles de usuario. Los identificadores son secuenciales... quizas puedas ver mas de lo que deberias.",
  "hint1":"Prueba distintos valores en /user/<id>.",
  "hint2":"El id 0 suele reservarse al administrador.",
  "hint3":"Consulta /user/0."},
 {"title":"Diagnostico de Red", "template":"web_cmdi", "category":"Web", "value":100,
  "cert":"Fundamentos de Pentesting (eJPT)", "domain":"Reconocimiento y Web", "difficulty":2,
  "description":"Herramienta de resolucion DNS. El parametro host se pasa a una shell del sistema.",
  "hint1":"Intenta encadenar un segundo comando con ;",
  "hint2":"Objetivo: leer /flag.txt",
  "hint3":"host=127.0.0.1; cat /flag.txt"},
 {"title":"Visor de Documentos", "template":"web_lfi", "category":"Web", "value":100,
  "cert":"Fundamentos de Pentesting (eJPT)", "domain":"Reconocimiento y Web", "difficulty":2,
  "description":"Visor de documentos que lee ficheros por nombre. El parametro page no se valida.",
  "hint1":"El parametro page se concatena a una ruta del disco.",
  "hint2":"Usa traversal ../ para salir del directorio.",
  "hint3":"Necesitas tres niveles: ?page=../../../flag.txt"},
]

for spec in SPECS:
    slug = None
    g = bus.call("creador", "generate_challenge", spec)
    slug = g["slug"]
    v = bus.call("validador", "validate_challenge", {"slug": slug})
    print("== %s | validado=%s" % (slug, v.get("success")))
    if v.get("success"):
        bus.call("mentor", "approve_challenge", {"slug": slug, "by": "mentor"})
        p = bus.call("mentor", "publish_challenge", {"slug": slug})
        print("   publicado=%s cid=%s" % (p.get("success"), (p.get("loaded") or {}).get("challenge_id")))
    else:
        print("   detalle:", json.dumps(v)[:400])
