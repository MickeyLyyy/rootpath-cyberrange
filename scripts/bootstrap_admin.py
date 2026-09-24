import os, re, requests

BASE = "http://127.0.0.1:8000"
NAME  = os.environ["ADMIN_NAME"]
EMAIL = os.environ["ADMIN_EMAIL"]
PASS  = os.environ["ADMIN_PASSWORD"]

s = requests.Session()

def nonce_of(html):
    for pat in (r'name="nonce"[^>]*value="([^"]+)"', r'value="([^"]+)"[^>]*name="nonce"'):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None

r = s.get(BASE + "/setup", allow_redirects=False)
print("GET /setup ->", r.status_code, r.headers.get("Location"))
if r.status_code in (301, 302):
    print("SETUP_ALREADY_DONE")
else:
    n = nonce_of(r.text)
    data = {
        "nonce": n, "ctf_name": "RootPath",
        "ctf_description": "Plataforma de labs y retos por certificacion",
        "user_mode": "users", "name": NAME, "email": EMAIL, "password": PASS,
    }
    r2 = s.post(BASE + "/setup", data=data, allow_redirects=False)
    print("POST /setup ->", r2.status_code, r2.headers.get("Location"))

r = s.get(BASE + "/login")
n = nonce_of(r.text)
r = s.post(BASE + "/login", data={"name": NAME, "password": PASS, "nonce": n}, allow_redirects=False)
print("POST /login ->", r.status_code, r.headers.get("Location"))

r = s.get(BASE + "/")
n = nonce_of(r.text)
hdr = {"CSRF-Token": n or "", "Content-Type": "application/json"}

r = s.get(BASE + "/api/v1/users/me", headers=hdr)
print("GET /api/v1/users/me ->", r.status_code, r.text[:250])

r = s.post(BASE + "/api/v1/categories", headers=hdr, json={"name": "phase0", "type": "standard"})
print("POST /api/v1/categories ->", r.status_code, r.text[:250])

r = s.post(BASE + "/api/v1/tokens", headers=hdr, json={"expiration": "2030-01-01", "description": "bootstrap"})
print("POST /api/v1/tokens ->", r.status_code, r.text[:250])
if r.status_code == 200:
    open("/tmp/admin_token.txt", "w").write(r.json().get("value", ""))
    print("TOKEN_SAVED /tmp/admin_token.txt")
