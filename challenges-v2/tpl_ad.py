# -*- coding: utf-8 -*-
"""Builders AD (artefactos estáticos)."""
import base64, hashlib, hmac, json, os, secrets


# ---- NTLM (MD4) mínimo para Kerberoasting ----
def _md4(data):
    A, B, C, D = 0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476
    ml = len(data)
    data += b"\x80"
    while len(data) % 64 != 56:
        data += b"\x00"
    data += (ml * 8).to_bytes(8, "little")

    def rol(x, n):
        return ((x << n) | (x >> (32 - n))) & 0xffffffff

    for i in range(0, len(data), 64):
        X = [int.from_bytes(data[i + j:i + j + 4], "little") for j in range(0, 64, 4)]
        a, b, c, d = A, B, C, D
        for j in range(16):
            k = j; s = [3, 7, 11, 19][j % 4]; f = (b & c) | (~b & d)
            a = rol((a + f + X[k]) & 0xffffffff, s); a, b, c, d = d, a, b, c
        for j in range(16):
            k = (j % 4) * 4 + j // 4; s = [3, 5, 9, 13][j % 4]; f = (b & c) | (b & d) | (c & d)
            a = rol((a + f + X[k] + 0x5a827999) & 0xffffffff, s); a, b, c, d = d, a, b, c
        for j in range(16):
            k = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15][j]; s = [3, 9, 11, 15][j % 4]
            f = b ^ c ^ d
            a = rol((a + f + X[k] + 0x6ed9eba1) & 0xffffffff, s); a, b, c, d = d, a, b, c
        A = (A + a) & 0xffffffff; B = (B + b) & 0xffffffff
        C = (C + c) & 0xffffffff; D = (D + d) & 0xffffffff
    return A.to_bytes(4, "little") + B.to_bytes(4, "little") + C.to_bytes(4, "little") + D.to_bytes(4, "little")


def _nt_hash(pw):
    return _md4(pw.encode("utf-16-le"))


def _kerb_hash(password, user, realm, spn):
    key = _nt_hash(password)
    edata = os.urandom(48)
    checksum = hmac.new(key, edata, hashlib.md5).digest()
    return "$krb5tgs$23$*%s$%s$%s*$%s$%s" % (user, realm, spn, checksum.hex(), edata.hex())


def _t_ad_ldap(spec, flag):
    ldif = (
        "dn: cn=admin,dc=rootpath,dc=local\ncn: admin\n\n"
        "dn: cn=svc_backup,cn=Users,dc=rootpath,dc=local\ncn: svc_backup\n"
        "sAMAccountName: svc_backup\ndescription:: %s\n\n"
        "dn: cn=j.smith,cn=Users,dc=rootpath,dc=local\ncn: j.smith\n"
        "description: usuario estandar\n\n"
    ) % base64.b64encode(flag.encode()).decode()
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, base64, re\n"
             "s = open(sys.argv[1], errors='ignore').read()\n"
             "for m in re.finditer(r'^description:: (.+)$', s, re.M):\n"
             "    try:\n"
             "        d = base64.b64decode(m.group(1)).decode(errors='ignore')\n"
             "        if 'RP{' in d:\n"
             "            print(d.strip())\n"
             "    except Exception:\n"
             "        pass\n"
             "PY\n")
    note = "Los atributos binarios en LDIF van con '::' (Base64). Decodifica el description de svc_backup."
    return {"artifacts/ldap_dump.ldif": ldif}, solve, \
        {"kind": "static", "file": "ldap_dump.ldif", "connection": "Adjunto: ldap_dump.ldif"}, note


def _t_ad_bloodhound(spec, flag):
    nodes = {
        "users": [
            {"name": "ADMINISTRATOR@ROOTPATH.LOCAL", "properties": {"admincount": 1}},
            {"name": "HELPDESK@ROOTPATH.LOCAL", "properties": {"description": base64.b64encode(b"cuenta de soporte").decode()}},
            {"name": "J.SMITH@ROOTPATH.LOCAL", "properties": {"description": base64.b64encode(flag.encode()).decode()}},
            {"name": "SVC_BACKUP@ROOTPATH.LOCAL", "properties": {"description": base64.b64encode(b"servicio de backups").decode()}},
        ],
        "groups": [{"name": "DOMAIN ADMINS@ROOTPATH.LOCAL"}, {"name": "DOMAIN CONTROLLERS@ROOTPATH.LOCAL"}],
        "computers": [{"name": "DC01.ROOTPATH.LOCAL"}],
        "edges": [
            {"source": "J.SMITH@ROOTPATH.LOCAL", "target": "DOMAIN CONTROLLERS@ROOTPATH.LOCAL", "label": "AdminTo"},
            {"source": "HELPDESK@ROOTPATH.LOCAL", "target": "J.SMITH@ROOTPATH.LOCAL", "label": "GenericAll"},
        ],
    }
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, json, base64\n"
             "d = json.load(open(sys.argv[1]))\n"
             "for e in d.get('edges', []):\n"
             "    if e.get('label') == 'AdminTo' and 'DOMAIN CONTROLLERS' in e.get('target', ''):\n"
             "        for u in d['users']:\n"
             "            if u['name'] == e['source']:\n"
             "                print(base64.b64decode(u['properties']['description']).decode())\n"
             "PY\n")
    note = "Recorre los edges buscando AdminTo hacia DOMAIN CONTROLLERS y decodifica la description del usuario origen."
    return {"artifacts/bloodhound.json": json.dumps(nodes, indent=2)}, solve, \
        {"kind": "static", "file": "bloodhound.json", "connection": "Adjunto: bloodhound.json"}, note


def _t_ad_kerberoast(spec, flag):
    pw = spec["spec"]["password"]
    user = spec["spec"]["user"]
    realm = spec["spec"]["realm"]
    spn = spec["spec"]["spn"]
    kh = _kerb_hash(pw, user, realm, spn)
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, hashlib, hmac\n"
             "def md4(data):\n"
             "    A,B,C,D = 0x67452301,0xefcdab89,0x98badcfe,0x10325476\n"
             "    ml = len(data); data += b'\\x80'\n"
             "    while len(data) % 64 != 56: data += b'\\x00'\n"
             "    data += (ml*8).to_bytes(8,'little')\n"
             "    rol = lambda x,n: ((x<<n)|(x>>(32-n))) & 0xffffffff\n"
             "    for i in range(0,len(data),64):\n"
             "        X=[int.from_bytes(data[i+j:i+j+4],'little') for j in range(0,64,4)]\n"
             "        a,b,c,d=A,B,C,D\n"
             "        for j in range(16):\n"
             "            k=j; s=[3,7,11,19][j%4]; f=(b&c)|(~b&d)\n"
             "            a=rol((a+f+X[k])&0xffffffff,s); a,b,c,d=d,a,b,c\n"
             "        for j in range(16):\n"
             "            k=(j%4)*4+j//4; s=[3,5,9,13][j%4]; f=(b&c)|(b&d)|(c&d)\n"
             "            a=rol((a+f+X[k]+0x5a827999)&0xffffffff,s); a,b,c,d=d,a,b,c\n"
             "        for j in range(16):\n"
             "            k=[0,8,4,12,2,10,6,14,1,9,5,13,3,11,7,15][j]; s=[3,9,11,15][j%4]\n"
             "            f=b^c^d; a=rol((a+f+X[k]+0x6ed9eba1)&0xffffffff,s); a,b,c,d=d,a,b,c\n"
             "        A=(A+a)&0xffffffff; B=(B+b)&0xffffffff; C=(C+c)&0xffffffff; D=(D+d)&0xffffffff\n"
             "    return A.to_bytes(4,'little')+B.to_bytes(4,'little')+C.to_bytes(4,'little')+D.to_bytes(4,'little')\n"
             "def nt(pw): return md4(pw.encode('utf-16-le'))\n"
             "line = open(sys.argv[1]).read().strip()\n"
             "parts = line.split('$'); checksum = bytes.fromhex(parts[6]); edata = bytes.fromhex(parts[7])\n"
             "words = ['password','backup2023','Summer2023!','P@ssw0rd','rootpath2024','Winter2024!','svcpass']\n"
             "for w in words:\n"
             "    if hmac.new(nt(w), edata, hashlib.md5).digest() == checksum:\n"
             "        print('RP{" + user + "_%s}' % w); break\n"
             "PY\n")
    note = "Crackea el hash Kerberoast (RC4-HMAC) contra una wordlist pequena; la bandera es RP{usuario_contrasena}."
    return {"artifacts/kerberoast.txt": kh + "\n"}, solve, \
        {"kind": "static", "file": "kerberoast.txt", "connection": "Adjunto: kerberoast.txt"}, note


BUILDERS = {
    "ad_ldap": _t_ad_ldap,
    "ad_bloodhound": _t_ad_bloodhound,
    "ad_kerberoast": _t_ad_kerberoast,
}
