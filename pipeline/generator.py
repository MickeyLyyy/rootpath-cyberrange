import os, re, json, time, socket, secrets
import templates, state
PIPE = os.path.dirname(os.path.abspath(__file__))
STAGING = os.path.join(PIPE, "staging")

def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def gen_flag(slug):
    return "RP{%s_%s}" % (re.sub(r'[^a-z0-9]','_',slug)[:24], secrets.token_hex(3))
def next_free_port(start=8090):
    used = {v.get("port") for v in state.load().values() if v.get("port")}
    p = start
    while True:
        if p in used:
            p += 1; continue
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p)); s.close(); return p
        except OSError:
            s.close(); p += 1

def generate(spec):
    slug = spec.get("slug") or slugify(spec["title"])
    d = os.path.join(STAGING, slug)
    os.makedirs(os.path.join(d, "solution"), exist_ok=True)
    flag = spec.get("flag") or gen_flag(slug)
    files, solve, meta, neg = templates.build(spec["template"], spec, flag)
    for name, content in files.items():
        p = os.path.join(d, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(content)
    open(os.path.join(d, "solve.sh"), "w").write(solve)
    os.chmod(os.path.join(d, "solve.sh"), 0o755)
    open(os.path.join(d, "solution", "writeup.md"), "w").write(templates.writeup(spec, flag))
    open(os.path.join(d, "challenge.yml"), "w").write(templates.challenge_yml(spec, slug, flag))
    port = next_free_port() if meta["kind"] == "service" else None
    meta.update({"slug": slug, "flag": flag, "spec": spec, "host_port": port,
                 "neg_help": neg, "created": time.time()})
    open(os.path.join(d, "meta.json"), "w").write(json.dumps(meta, indent=2))
    state.set_state(slug, "draft", title=spec["title"], category=spec["category"],
                    value=spec["value"], template=spec["template"], cert=spec.get("cert"),
                    domain=spec.get("domain"), port=port, flag=flag)
    return {"slug": slug, "dir": d, "flag": flag, "meta": meta}
