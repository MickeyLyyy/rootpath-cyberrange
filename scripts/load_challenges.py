import re, json, requests, sys

HOST = "172.170.10.11"
BASE = f"http://{HOST}:8000"
TOK = open("/opt/rootpath/.admin_token").read().strip()
H = {"Authorization": "Token " + TOK, "Content-Type": "application/json"}

s = requests.Session()
r = s.get(BASE + "/api/v1/users/me", headers=H)
if r.status_code != 200:
    print("AUTH FAIL", r.status_code, r.text[:200]); sys.exit(1)
print("AUTH OK como", r.json()["data"]["name"])

CH = [
 dict(name="Comentario Revelador", cat="Web", val=50,
      desc=f"Tienda simple en http://{HOST}:8081/ . A veces los desarrolladores dejan notas que no deberian.",
      flag="RP{comment_l34ks_ar3_fun}", conn=f"http://{HOST}:8081/",
      hint="Mira el codigo fuente HTML de la pagina (Ctrl+U)."),
 dict(name="Robots Curiosos", cat="Web", val=50,
      desc=f"Intranet en http://{HOST}:8082/ . Los buscadores reciben instrucciones... quizas te sirvan a ti tambien.",
      flag="RP{r0b0ts_txt_n3v3r_l1es}", conn=f"http://{HOST}:8082/",
      hint="Revisa /robots.txt."),
 dict(name="Inclusion Local", cat="Web", val=100,
      desc=f"Visor de paginas en http://{HOST}:8083/?page=home . El parametro 'page' se pasa directamente al disco.",
      flag="RP{lfi_p4th_tr4v3rs4l}", conn=f"http://{HOST}:8083/?page=home",
      hint="Sube directorios con ../ hasta llegar a /flag.txt (ojo con la profundidad)."),
 dict(name="Login Bypass", cat="Web", val=100,
      desc=f"Panel de login en http://{HOST}:8084/ . Usa parametros GET u y p. La consulta se construye concatenando.",
      flag="RP{sqli_0r_1_3qu4ls_1}", conn=f"http://{HOST}:8084/",
      hint="Cierra la comilla y comenta el resto con -- ."),
 dict(name="Ping Injection", cat="Web", val=100,
      desc=f"Utilidad de ping en http://{HOST}:8085/?host=127.0.0.1 . El servidor ejecuta el comando en una shell.",
      flag="RP{cmd_1nj3ct10n_pwn3d}", conn=f"http://{HOST}:8085/?host=127.0.0.1",
      hint="Encadena un segundo comando con ; para leer /flag.txt."),
 dict(name="SUID Peligroso", cat="Linux", val=200,
      desc=f"SSH: ssh player@{HOST} -p 2201 (password: player). Encuentra el binario SUID y escala a root.",
      flag="RP{su1d_b1n4ry_pr1v3sc}", conn=f"ssh player@{HOST} -p 2201",
      hint="find / -perm -4000 -type f 2>/dev/null"),
 dict(name="Cron Ajeno", cat="Linux", val=200,
      desc=f"SSH: ssh player@{HOST} -p 2202 (password: player). Un proceso root ejecuta periodicamente un script modificable.",
      flag="RP{cr0n_j0b_wr1t4bl3}", conn=f"ssh player@{HOST} -p 2202",
      hint="Revisa /etc/cron.d y los permisos de los scripts que ejecuta."),
 dict(name="Capas de Base64", cat="Crypto", val=50,
      desc="Adjunto: base64_layers.txt . El secreto esta codificado en Base64 tres veces.",
      flag="RP{b4s364_l4y3rs_d3c0d3d}", file="base64_layers.txt", conn=None,
      hint="Decodifica Base64 tres veces."),
 dict(name="Cesar Antiguo", cat="Crypto", val=50,
      desc="Adjunto: caesar.txt . Cifrado clasico con desplazamiento pequeno.",
      flag="RP{c4es4r_sh1ft_3}", file="caesar.txt", conn=None,
      hint="Prueba todos los desplazamientos (ROT)."),
 dict(name="Strings Ocultas", cat="Forensics", val=100,
      desc="Adjunto: evidencia.bin . Volcado binario con la flag escondida entre los datos.",
      flag="RP{str1ngs_4lw4ys_w1ns}", file="evidencia.bin", conn=None,
      hint="Usa 'strings' y busca RP{...}."),
]

created = 0
for c in CH:
    r = s.post(BASE + "/api/v1/challenges", headers=H, json={
        "name": c["name"], "category": c["cat"], "description": c["desc"],
        "value": c["val"], "type": "standard", "state": "visible"})
    if r.status_code != 200:
        print(f"[FAIL] {c['name']}: {r.status_code} {r.text[:180]}"); continue
    cid = r.json()["data"]["id"]
    rf = s.post(BASE + "/api/v1/flags", headers=H,
                json={"challenge_id": cid, "content": c["flag"], "type": "static", "data": "case_insensitive"})
    rh = s.post(BASE + "/api/v1/hints", headers=H,
                json={"challenge_id": cid, "content": c["hint"], "cost": 5})
    fmsg = "sin adjunto"
    if c.get("file"):
        path = f"/opt/rootpath/challenges/static/{c['file']}"
        with open(path, "rb") as fh:
            rf2 = requests.post(BASE + "/api/v1/files",
                                headers={"Authorization": "Token " + TOK},
                                data={"type": "challenge", "challenge_id": str(cid)},
                                files={"file": (c["file"], fh)})
        if rf2.status_code == 200:
            loc = rf2.json()["data"][0]["location"]
            s.patch(BASE + f"/api/v1/challenges/{cid}", headers=H, json={"files": [loc]})
            fmsg = "adjunto OK"
        else:
            fmsg = f"adjunto FAIL {rf2.status_code} {rf2.text[:100]}"
    created += 1
    print(f"[OK] id={cid} {c['name']} ({c['cat']},{c['val']}) flag={rf.status_code} hint={rh.status_code} {fmsg}")

print(f"\nRetos creados: {created}/{len(CH)}")
r = s.get(BASE + "/api/v1/challenges?view=admin", headers=H)
print("Total en CTFd:", r.json().get("meta", {}).get("count", "?"))
