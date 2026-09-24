import json
p = "/opt/rootpath/runtime/lab_map.json"
m = json.load(open(p, encoding="utf-8"))
m["NimbusDrive - Almacenamiento en la Nube"] = {
    "service": "nimbusdrive", "image": "rootpath-v2-nimbusdrive",
    "internal_port": 5000, "kind": "web",
}
json.dump(m, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("lab_map:", len(m), "entradas")
