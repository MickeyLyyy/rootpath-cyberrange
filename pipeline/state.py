import json, os
PIPE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(PIPE, "pipeline.json")
def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}
def save(d):
    json.dump(d, open(STATE, "w"), indent=2)
def get(slug):
    return load().get(slug)
def set_state(slug, st, **extra):
    d = load(); e = d.get(slug, {}); e["state"] = st; e.update(extra); d[slug] = e; save(d); return e
