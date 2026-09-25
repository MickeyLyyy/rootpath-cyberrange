import sys, re
import requests
PORT = int(sys.argv[1])
B = "http://172.170.10.11:%d" % PORT
r = requests.get(B + "/item/9", timeout=8).json()
print("item:", r)
m = re.search(r"RP\{[^}]*\}", str(r))
print("FLAG:", m.group(0) if m else "(no encontrada)")
