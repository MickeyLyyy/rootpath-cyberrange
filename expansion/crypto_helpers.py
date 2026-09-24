import hashlib, hmac, os, base64

def _md4(data: bytes) -> bytes:
    # MD4 puro en Python (para NTLM)
    A, B, C, D = 0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476
    ml = len(data)
    data += b"\x80"
    while len(data) % 64 != 56:
        data += b"\x00"
    data += (ml * 8).to_bytes(8, "little")
    def rol(x, n): return ((x << n) | (x >> (32 - n))) & 0xffffffff
    for i in range(0, len(data), 64):
        X = [int.from_bytes(data[i + j:i + j + 4], "little") for j in range(0, 64, 4)]
        a, b, c, d = A, B, C, D
        for j in range(16):
            k = j; s = [3,7,11,19][j % 4]
            f = (b & c) | (~b & d)
            a = rol((a + f + X[k]) & 0xffffffff, s)
            a, b, c, d = d, a, b, c
        for j in range(16):
            k = (j % 4) * 4 + j // 4; s = [3,5,9,13][j % 4]
            f = (b & c) | (b & d) | (c & d)
            a = rol((a + f + X[k] + 0x5a827999) & 0xffffffff, s)
            a, b, c, d = d, a, b, c
        for j in range(16):
            k = [0,8,4,12,2,10,6,14,1,9,5,13,3,11,7,15][j]; s = [3,9,11,15][j % 4]
            f = b ^ c ^ d
            a = rol((a + f + X[k] + 0x6ed9eba1) & 0xffffffff, s)
            a, b, c, d = d, a, b, c
        A = (A + a) & 0xffffffff; B = (B + b) & 0xffffffff
        C = (C + c) & 0xffffffff; D = (D + d) & 0xffffffff
    return A.to_bytes(4, "little") + B.to_bytes(4, "little") + C.to_bytes(4, "little") + D.to_bytes(4, "little")

def nt_hash(pw: str) -> bytes:
    return _md4(pw.encode("utf-16-le"))

def kerb_hash(password: str, user: str, realm: str, spn: str, etype=23):
    key = nt_hash(password)
    edata = os.urandom(48)
    checksum = hmac.new(key, edata, hashlib.md5).digest()
    if etype == 23:
        return "$krb5tgs$23$*%s$%s$%s*$%s$%s" % (user, realm, spn, checksum.hex(), edata.hex())
    return None

def asrep_hash(password: str, user: str, realm: str):
    key = nt_hash(password); edata = os.urandom(40)
    checksum = hmac.new(key, edata, hashlib.md5).digest()
    return "$krb5asrep$23$%s@%s:%s$%s" % (user, realm, checksum.hex(), edata.hex())

def crack(line: str, wordlist):
    if line.startswith("$krb5tgs$"):
        parts = line.split("$"); checksum = bytes.fromhex(parts[6]); edata = bytes.fromhex(parts[7])
    else:
        body = line.split(":", 1)[1]
        checksum = bytes.fromhex(body.split("$")[0]); edata = bytes.fromhex(body.split("$")[1])
    for w in wordlist:
        if hmac.new(nt_hash(w), edata, hashlib.md5).digest() == checksum:
            return w
    return None

CRACKER = r'''
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
'''
open("/opt/rootpath/expansion/cracker.py", "w").write(CRACKER)
print("crypto_helpers + cracker OK")
