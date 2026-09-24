# -*- coding: utf-8 -*-
"""Builders Blue Team (artefactos estáticos)."""
import base64


def _t_blue_weblog(spec, flag):
    enc = base64.b64encode(flag.encode()).decode()
    log = (
        "203.0.113.10 - - [10/Aug/2026:03:14:01 +0000] \"GET /index.php HTTP/1.1\" 200 1043\n"
        "203.0.113.10 - - [10/Aug/2026:03:14:02 +0000] \"GET /login.php HTTP/1.1\" 200 812\n"
        "198.51.100.77 - - [10/Aug/2026:03:15:10 +0000] \"GET /admin HTTP/1.1\" 403 153\n"
        "198.51.100.77 - - [10/Aug/2026:03:15:44 +0000] \"POST /api/export?data=%s HTTP/1.1\" 200 88\n"
        "203.0.113.10 - - [10/Aug/2026:03:16:00 +0000] \"GET /index.php HTTP/1.1\" 200 1043\n"
    ) % enc
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, re, base64\n"
             "for m in re.finditer(r'data=([A-Za-z0-9+/=]+)', open(sys.argv[1]).read()):\n"
             "    try:\n"
             "        d = base64.b64decode(m.group(1)).decode()\n"
             "        if 'RP{' in d:\n"
             "            print(d)\n"
             "    except Exception:\n"
             "        pass\n"
             "PY\n")
    note = "Busca la peticion POST anomala (/api/export) y decodifica el parametro 'data' en Base64."
    return {"artifacts/access.log": log}, solve, \
        {"kind": "static", "file": "access.log", "connection": "Adjunto: access.log"}, note


def _t_blue_authlog(spec, flag):
    enc = base64.b64encode(flag.encode()).decode()
    lines = []
    for i in range(6):
        lines.append("Aug 10 03:0%d:1%d server sshd[%d]: Failed password for invalid user admin from 203.0.113.66 port %d ssh2"
                     % (i, i, 1000 + i, 40000 + i))
    lines.append("Aug 10 03:02:10 server sshd[1100]: Accepted password for webadmin from 203.0.113.66 port 44444 ssh2")
    lines.append("Aug 10 03:02:44 server sudo: webadmin : TTY=pts/0 ; PWD=/var/www ; USER=root ; "
                 "COMMAND=/bin/bash -c \"echo %s > /tmp/.cache\"" % enc)
    lines.append("Aug 10 03:03:01 server sshd[1100]: pam_unix(sshd:session): session closed for user webadmin")
    authlog = "\n".join(lines) + "\n"
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, re, base64\n"
             "for line in open(sys.argv[1]):\n"
             "    for m in re.finditer(r'echo ([A-Za-z0-9+/=]+) >', line):\n"
             "        print(base64.b64decode(m.group(1)).decode())\n"
             "PY\n")
    note = "Correlaciona el acceso exitoso y revisa las lineas sudo: el comando incluye un valor Base64 tras 'echo'."
    return {"artifacts/auth.log": authlog}, solve, \
        {"kind": "static", "file": "auth.log", "connection": "Adjunto: auth.log"}, note


def _t_blue_dns(spec, flag):
    b = base64.b32encode(flag.encode()).decode().rstrip("=").lower()
    chunks = [b[i:i + 16] for i in range(0, len(b), 16)]
    dns = ["# Zeek dns.log (columnas: ts id orig query)"] + [
        "%.3f\tC1\t203.0.113.66\t%s.exfil.rootpath.local" % (1.0 + i, c) for i, c in enumerate(chunks)
    ]
    dnslog = "\n".join(dns) + "\n"
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, re, base64\n"
             "labels = []\n"
             "for line in open(sys.argv[1]):\n"
             "    m = re.search(r'\\t([a-z2-7]+)\\.exfil\\.rootpath\\.local', line)\n"
             "    if m:\n"
             "        labels.append(m.group(1))\n"
             "data = ''.join(labels).upper()\n"
             "pad = '=' * ((8 - len(data) % 8) % 8)\n"
             "print(base64.b32decode(data + pad).decode())\n"
             "PY\n")
    note = "Reensambla los labels de los subdominios y decodifica Base32."
    return {"artifacts/dns.log": dnslog}, solve, \
        {"kind": "static", "file": "dns.log", "connection": "Adjunto: dns.log"}, note


BUILDERS = {
    "blue_weblog": _t_blue_weblog,
    "blue_authlog": _t_blue_authlog,
    "blue_dns": _t_blue_dns,
}
