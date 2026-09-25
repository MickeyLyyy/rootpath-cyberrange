import json
p = "/opt/rootpath/runtime/lab_map.json"
m = json.load(open(p))
m["Colmado - Panel de Diagnostico"] = {
    "kind": "machine",
    "service": "colmado",
    "target_image": "rootpath-v2-colmado",
    "attacker_image": "rootpath-attacker",
    "target_port": 8080,
}
json.dump(m, open(p, "w"), indent=2, ensure_ascii=False)
print("entradas lab_map:", len(m))
