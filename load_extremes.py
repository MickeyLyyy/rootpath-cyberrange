import requests
B = "http://127.0.0.1:8000"
TOK = open("/opt/rootpath/.admin_token").read().strip()
AGENT = open("/opt/rootpath/runtime/agent_key").read().strip()
H = {"Authorization": "Token " + TOK, "Content-Type": "application/json"}

CHALLS = [
    {"name": "BancoQuisqueya - Banca Digital", "slug": "bqdigital",
     "desc": ("ROOTPATH // EXPEDIENTE RD-052\n\n"
              "**Incidente:** Acceso no autorizado al generador de reportes de la banca digital de una entidad financiera local.\n"
              "**Dificultad:** Extremo\n\n"
              "El portal emite tokens firmados (JWT) y publica sus metadatos de firma. Escala a un rol administrativo y recupera la bandera.\n\n"
              "**Conexion:** pulsa **Abrir** en *Entorno* para desplegar tu propia instancia.\n\nFormato: RP{...}"),
     "hints": ["Los metadatos de firma son publicos y estandar (/.well-known).",
               "Un token no es mas que tres trozos separados por puntos.",
               "El generador bloquea ciertas palabras... pero no lo que viaja en la URL."]},
    {"name": "LuzClara Telecom - Facturacion Electronica (e-CF)", "slug": "luzclara",
     "desc": ("ROOTPATH // EXPEDIENTE RD-053\n\n"
              "**Incidente:** Validador de comprobantes fiscales (e-CF) de una operadora de telecomunicaciones con fuga de datos internos.\n"
              "**Dificultad:** Extremo\n\n"
              "El validador procesa XML y cuenta con un WAF corporativo. Elude las protecciones, alcanza el servicio interno de diagnostico y recupera la bandera.\n\n"
              "**Conexion:** pulsa **Abrir** en *Entorno*.\n\nFormato: RP{...}"),
     "hints": ["El WAF revisa los bytes tal cual llegan.",
               "El validador procesa DTDs externos.",
               "El diagnostico de red solo alcanza destinos internos."]},
    {"name": "EDQ Energia - Portal de Servicios", "slug": "edqenergia",
     "desc": ("ROOTPATH // EXPEDIENTE RD-054\n\n"
              "**Incidente:** Portal de servicios de una distribuidora electrica con expedientes expuestos.\n"
              "**Dificultad:** Extremo\n\n"
              "La consulta de expedientes revela mas de la cuenta. Obten la clave de la API administrativa y explota el motor de solicitudes YAML para recuperar la bandera.\n\n"
              "**Conexion:** pulsa **Abrir** en *Entorno*.\n\nFormato: RP{...}"),
     "hints": ["La consulta de expediente no verifica quien pregunta.",
               "Los codigos de cliente son consecutivos.",
               "El portal interpreta YAML sin restricciones."]},
]

existing = {c["name"]: c["id"] for c in
            requests.get(B + "/api/v1/challenges?view=admin", headers=H).json()["data"]}

for ch in CHALLS:
    if ch["name"] in existing:
        cid = existing[ch["name"]]
        print("existe cid =", cid, "-", ch["name"])
    else:
        r = requests.post(B + "/api/v1/challenges", headers=H, json={
            "name": ch["name"], "category": "Web", "description": ch["desc"],
            "value": 250, "type": "standard", "state": "visible"})
        cid = r.json()["data"]["id"]
        print("creado cid =", cid, "-", ch["name"])
        requests.post(B + "/api/v1/flags", headers=H, json={
            "challenge_id": cid, "type": "rootpath", "content": ch["slug"], "data": ""})
        for i, h in enumerate(ch["hints"]):
            requests.post(B + "/api/v1/hints", headers=H, json={
                "challenge_id": cid, "content": h, "cost": [10, 20, 40][i]})
    mr = requests.post(B + "/plugins/rootpath/api/agent/map", headers={
        "Authorization": "Token " + TOK, "X-Agent-Key": AGENT,
        "Content-Type": "application/json"},
        json={"challenge_name": ch["name"], "domain_name": "Explotacion Web Avanzada"})
    print("  map:", mr.status_code, mr.text[:80])
print("LISTO")
