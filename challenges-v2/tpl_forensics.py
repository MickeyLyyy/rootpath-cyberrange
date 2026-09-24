# -*- coding: utf-8 -*-
"""Builders Forensics (artefactos estáticos)."""
import base64, os, struct, zlib


def _png_chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))


def _make_png(flag, w=8, h=8):
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    # imagen RGB simple (degradado)
    raw = b""
    for y in range(h):
        row = b"\x00"
        for x in range(w):
            row += bytes([x * 32 % 256, y * 32 % 256, (x + y) * 16 % 256])
        raw += row
    idat = _png_chunk(b"IDAT", zlib.compress(raw))
    text = _png_chunk(b"tEXt", b"Comment\x00" + flag.encode())
    iend = _png_chunk(b"IEND", b"")
    return sig + ihdr + text + idat + iend


def _t_forensics_strings(spec, flag):
    data = os.urandom(1200)
    idx = 400
    data = data[:idx] + flag.encode() + data[idx + len(flag):]
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, re\n"
             "d = open(sys.argv[1], 'rb').read()\n"
             "for m in re.findall(rb'RP\\{[^}]+\\}', d):\n"
             "    print(m.decode())\n"
             "PY\n")
    note = "Busca cadenas ASCII legibles (tecnica 'strings') y localiza el patron RP{...}."
    return {"artifacts/evidencia.bin": data}, solve, \
        {"kind": "static", "file": "evidencia.bin", "connection": "Adjunto: evidencia.bin"}, note


def _t_forensics_meta(spec, flag):
    png = _make_png(flag)
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, struct, zlib\n"
             "d = open(sys.argv[1], 'rb').read()\n"
             "i = 8\n"
             "while i + 8 <= len(d):\n"
             "    ln = struct.unpack('>I', d[i:i+4])[0]\n"
             "    typ = d[i+4:i+8]\n"
             "    data = d[i+8:i+8+ln]\n"
             "    if typ == b'tEXt':\n"
             "        print(data.split(b'\\x00', 1)[1].decode())\n"
             "    i += 12 + ln\n"
             "PY\n")
    note = "Inspecciona los chunks del PNG (en particular tEXt) para leer el texto incrustado en los metadatos."
    return {"artifacts/foto.png": png}, solve, \
        {"kind": "static", "file": "foto.png", "connection": "Adjunto: foto.png"}, note


def _make_pcap(flag):
    b64 = base64.b64encode(flag.encode()).decode()
    hdr = struct.pack("<IHHiIII", 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
    def pkt(ts, payload):
        return struct.pack("<IIII", ts, 0, len(payload), len(payload)) + payload
    noise1 = b"GET /index.html HTTP/1.1\r\nHost: portal.rd\r\nUser-Agent: Mozilla/5.0\r\n\r\n"
    exfil = ("GET /api/export?data=%s HTTP/1.1\r\nHost: portal.rd\r\n\r\n" % b64).encode()
    noise2 = b"GET /style.css HTTP/1.1\r\nHost: portal.rd\r\n\r\n"
    return hdr + pkt(1000, noise1) + pkt(1001, exfil) + pkt(1002, noise2)


def _t_forensics_pcap(spec, flag):
    pcap = _make_pcap(flag)
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, re, base64\n"
             "d = open(sys.argv[1], 'rb').read()\n"
             "for m in re.findall(rb'data=([A-Za-z0-9+/=]+)', d):\n"
             "    try:\n"
             "        s = base64.b64decode(m).decode()\n"
             "        if 'RP{' in s:\n"
             "            print(s)\n"
             "    except Exception:\n"
             "        pass\n"
             "PY\n")
    note = "Analiza el pcap y localiza la peticion GET con el parametro 'data' en Base64. Decodificalo."
    return {"artifacts/trafico.pcap": pcap}, solve, \
        {"kind": "static", "file": "trafico.pcap", "connection": "Adjunto: trafico.pcap"}, note


BUILDERS = {
    "forensics_strings": _t_forensics_strings,
    "forensics_meta": _t_forensics_meta,
    "forensics_pcap": _t_forensics_pcap,
}
