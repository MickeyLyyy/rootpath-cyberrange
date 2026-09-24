
import sys, hmac, hashlib
sys.path.insert(0, "/opt/rootpath/expansion")
from crypto_helpers import nt_hash
line = open(sys.argv[1]).read().strip()
if line.startswith("$krb5tgs$"):
    parts = line.split("$"); checksum = bytes.fromhex(parts[6]); edata = bytes.fromhex(parts[7])
else:
    body = line.split(":", 1)[1]
    checksum = bytes.fromhex(body.split("$")[0]); edata = bytes.fromhex(body.split("$")[1])
words = ["password","backup2023","Summer2023!","P@ssw0rd","rootpath2024","Winter2024!","svcpass"]
for w in words:
    if hmac.new(nt_hash(w), edata, hashlib.md5).digest() == checksum:
        print("RP{%s_%s}" % (sys.argv[2], w)); sys.exit(0)
print("no encontrado"); sys.exit(1)
