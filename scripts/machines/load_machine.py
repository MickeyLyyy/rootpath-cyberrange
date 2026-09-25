import requests
B = "http://127.0.0.1:8000"
TOK = open("/opt/rootpath/.admin_token").read().strip()
AGENT = open("/opt/rootpath/runtime/agent_key").read().strip()
H = {"Authorization": "Token " + TOK, "Content-Type": "application/json"}
NAME = "Colmado - Panel de Diagnostico"
DESC = ("ROOTPATH // MAQUINA RD-001\n\n"
        "**Escenario:** portal de diagnostico de un colmado online.\n"
        "**Dificultad:** Media\n\n"
        "Maquina boot2root: enumera los servicios, explota la aplicacion web, "
        "escala privilegios hasta root y lee la bandera.\n\n"
        "**Conexion:** pulsa **Abrir** para desplegar tu terminal de atacante y tu objetivo.\n\n"
        "Formato: RP{...}")
existing = {c["name"]: c["id"] for c in
            requests.get(B + "/api/v1/challenges?view=admin", headers=H).json()["data"]}
if NAME in existing:
    cid = existing[NAME]; print("existe cid =", cid)
else:
    cid = requests.post(B + "/api/v1/challenges", headers=H, json={
        "name": NAME, "category": "Linux", "description": DESC,
        "value": 250, "type": "standard", "state": "visible"}).json()["data"]["id"]
    print("creado cid =", cid)
    requests.post(B + "/api/v1/flags", headers=H, json={
        "challenge_id": cid, "type": "rootpath", "content": "colmado", "data": ""})
    for i, h in enumerate(["nmap es tu primer paso.",
                           "La herramienta de diagnostico no valida la entrada.",
                           "Busca binarios con el bit SUID."]):
        requests.post(B + "/api/v1/hints", headers=H, json={
            "challenge_id": cid, "content": h, "cost": [10, 20, 40][i]})
mr = requests.post(B + "/plugins/rootpath/api/agent/map", headers={
    "Authorization": "Token " + TOK, "X-Agent-Key": AGENT, "Content-Type": "application/json"},
    json={"challenge_name": NAME, "domain_name": "Explotacion de Sistemas Linux"})
print("map:", mr.status_code, mr.text[:80])
print("LISTO", cid)
