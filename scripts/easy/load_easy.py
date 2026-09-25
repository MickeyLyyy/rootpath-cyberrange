import requests
B = "http://127.0.0.1:8000"
TOK = open("/opt/rootpath/.admin_token").read().strip()
AGENT = open("/opt/rootpath/runtime/agent_key").read().strip()
H = {"Authorization": "Token " + TOK, "Content-Type": "application/json"}

CHALLS = [
    {"name": "ArcadeScore - Tabla de Puntuaciones", "slug": "arcadescore", "value": 100,
     "desc": ("ROOTPATH // ARCADE RD-001\n\n"
              "**Incidente:** La tabla de puntuaciones de un arcade de la Zona Colonial esconde el premio del administrador.\n"
              "**Dificultad:** Facil\n\n"
              "Entra como administrador al panel de premios y reclama la bandera.\n\n"
              "**Conexion:** pulsa **Abrir** en *Entorno* para desplegar tu propia instancia.\n\nFormato: RP{...}"),
     "hints": ["El formulario de login concatena texto directo en la consulta."]},
    {"name": "SkinShop - Tienda de Skins", "slug": "skinshop", "value": 100,
     "desc": ("ROOTPATH // ARCADE RD-002\n\n"
              "**Incidente:** La tienda de skins de un battle royale local oculta un articulo fuera del catalogo visible.\n"
              "**Dificultad:** Facil\n\n"
              "Los articulos se consultan por identificador. Encuentra el que no se muestra y lee su descripcion.\n\n"
              "**Conexion:** pulsa **Abrir** en *Entorno*.\n\nFormato: RP{...}"),
     "hints": ["Prueba identificadores fuera del rango visible del catalogo."]},
    {"name": "SaveQuest - Visor de Partidas", "slug": "savequest", "value": 100,
     "desc": ("ROOTPATH // ARCADE RD-003\n\n"
              "**Incidente:** El visor de partidas de un RPG de 16 bits permite leer archivos fuera de la carpeta de saves.\n"
              "**Dificultad:** Facil\n\n"
              "Revisa como se solicitan los archivos y recuerda el clasico ../ para subir de directorio.\n\n"
              "**Conexion:** pulsa **Abrir** en *Entorno*.\n\nFormato: RP{...}"),
     "hints": ["La bandera vive en /flag.txt, en la raiz del sistema."]},
    {"name": "CraftWorld - Panel del Servidor", "slug": "craftworld", "value": 150,
     "desc": ("ROOTPATH // ARCADE RD-004\n\n"
              "**Incidente:** El panel de administracion de un servidor de supervivencia ejecuta comandos del sistema sin control.\n"
              "**Dificultad:** Facil\n\n"
              "La herramienta de diagnostico hace mas de lo que aparenta. Recupera la bandera del servidor.\n\n"
              "**Conexion:** pulsa **Abrir** en *Entorno*.\n\nFormato: RP{...}"),
     "hints": ["Un punto y coma ; permite encadenar otro comando en la consola."]},
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
            "value": ch["value"], "type": "standard", "state": "visible"})
        cid = r.json()["data"]["id"]
        print("creado cid =", cid, "-", ch["name"])
        requests.post(B + "/api/v1/flags", headers=H, json={
            "challenge_id": cid, "type": "rootpath", "content": ch["slug"], "data": ""})
        for i, h in enumerate(ch["hints"]):
            requests.post(B + "/api/v1/hints", headers=H, json={
                "challenge_id": cid, "content": h, "cost": 5})
    mr = requests.post(B + "/plugins/rootpath/api/agent/map", headers={
        "Authorization": "Token " + TOK, "X-Agent-Key": AGENT,
        "Content-Type": "application/json"},
        json={"challenge_name": ch["name"], "domain_name": "Reconocimiento y Web"})
    print("  map:", mr.status_code, mr.text[:80])
print("LISTO")
