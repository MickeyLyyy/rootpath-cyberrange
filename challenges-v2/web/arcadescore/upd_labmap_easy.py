import json
p = "/opt/rootpath/runtime/lab_map.json"
m = json.load(open(p))
for t, s in [("ArcadeScore - Tabla de Puntuaciones", "arcadescore"),
             ("SkinShop - Tienda de Skins", "skinshop"),
             ("SaveQuest - Visor de Partidas", "savequest"),
             ("CraftWorld - Panel del Servidor", "craftworld")]:
    m[t] = {"service": s, "image": "rootpath-v2-" + s,
            "internal_port": 5000, "kind": "web"}
json.dump(m, open(p, "w"), indent=2, ensure_ascii=False)
print("entradas lab_map:", len(m))
