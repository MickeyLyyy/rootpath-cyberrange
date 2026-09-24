# -*- coding: utf-8 -*-
"""Builders Crypto (artefactos estáticos)."""
import base64, random


def _vigenere(text, key, decrypt=False):
    out = []
    i = 0
    for c in text:
        if c.isalpha():
            k = ord(key[i % len(key)].lower()) - 97
            b = ord("A") if c.isupper() else ord("a")
            s = -k if decrypt else k
            out.append(chr((ord(c) - b + s) % 26 + b))
            i += 1
        else:
            out.append(c)
    return "".join(out)


def _t_crypto_base64(spec, flag):
    layers = spec["spec"].get("layers", 3)
    data = flag
    for _ in range(layers):
        data = base64.b64encode(data.encode()).decode()
    artifact = "Mensaje codificado en varias capas. Decodifica en cascada.\n\n" + data + "\n"
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, base64\n"
             "s = open(sys.argv[1]).read().splitlines()[-1]\n"
             "for _ in range(6):\n"
             "    try:\n"
             "        s = base64.b64decode(s).decode()\n"
             "    except Exception:\n"
             "        break\n"
             "print(s)\n"
             "PY\n")
    note = "Decodifica Base64 en cascada hasta obtener texto legible con la bandera."
    return {"artifacts/mensaje.txt": artifact}, solve, \
        {"kind": "static", "file": "mensaje.txt", "connection": "Adjunto: mensaje.txt"}, note


def _t_crypto_vigenere(spec, flag):
    key = spec["spec"].get("key", "rootpath")
    enc = _vigenere(flag, key)
    artifact = ("Mensaje cifrado con Vigenere.\n"
                "Nota: la clave es el nombre de la plataforma en minusculas.\n\n" + enc + "\n")
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys\n"
             "key = \"%s\"\n"
             "s = open(sys.argv[1]).read().splitlines()[-1]\n"
             "out = []; i = 0\n"
             "for c in s:\n"
             "    if c.isalpha():\n"
             "        k = ord(key[i %% len(key)]) - 97\n"
             "        b = ord('A') if c.isupper() else ord('a')\n"
             "        out.append(chr((ord(c) - b - k) %% 26 + b)); i += 1\n"
             "    else:\n"
             "        out.append(c)\n"
             "print(''.join(out))\n"
             "PY\n") % key
    note = "Cifrado Vigenere con clave 'rootpath'. Descifra cada letra restando el desplazamiento de la clave."
    return {"artifacts/carta.txt": artifact}, solve, \
        {"kind": "static", "file": "carta.txt", "connection": "Adjunto: carta.txt"}, note


def _mr(n, rounds=24):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _randprime(bits):
    while True:
        n = random.getrandbits(bits) | (1 << (bits - 1)) | 1
        if _mr(n):
            return n


def _nextprime(n):
    n |= 1
    while not _mr(n):
        n += 2
    return n


def _t_crypto_rsa(spec, flag):
    # primos cercanos -> factorizacion por Fermat; n grande para contener el flag
    p = _randprime(160)
    gap = random.randint(2, 1 << 20)
    q = _nextprime(p + gap)
    n = p * q
    e = 65537
    m = int.from_bytes(flag.encode(), "big")
    assert m < n
    c = pow(m, e, n)
    artifact = (
        "Mensaje cifrado con RSA (modulo factorizable por Fermat).\n"
        "n = %d\n"
        "e = %d\n"
        "c = %d\n" % (n, e, c)
    )
    solve = ("#!/usr/bin/env bash\n"
             "python3 - \"${FILE}\" <<'PY'\n"
             "import sys, re\n"
             "t = open(sys.argv[1]).read()\n"
             "n = int(re.search(r'n = (\\d+)', t).group(1))\n"
             "e = int(re.search(r'e = (\\d+)', t).group(1))\n"
             "c = int(re.search(r'c = (\\d+)', t).group(1))\n"
             "def isqrt(x):\n"
             "    if x < 0: raise ValueError\n"
             "    if x == 0: return 0\n"
             "    lo, hi = 0, x\n"
             "    while lo <= hi:\n"
             "        mid = (lo + hi) // 2\n"
             "        if mid * mid <= x: lo = mid + 1\n"
             "        else: hi = mid - 1\n"
             "    return hi\n"
             "a = isqrt(n) + 1\n"
             "while True:\n"
             "    b2 = a * a - n\n"
             "    b = isqrt(b2)\n"
             "    if b * b == b2:\n"
             "        p = a - b; q = a + b\n"
             "        break\n"
             "    a += 1\n"
             "phi = (p - 1) * (q - 1)\n"
             "d = pow(e, -1, phi)\n"
             "m = pow(c, d, n)\n"
             "print(m.to_bytes((m.bit_length() + 7) // 8, 'big').decode())\n"
             "PY\n")
    note = "n es factorizable por Fermat (primos cercanos). Factoriza, calcula phi y d, y descifra con m = pow(c, d, n)."
    return {"artifacts/rsa.txt": artifact}, solve, \
        {"kind": "static", "file": "rsa.txt", "connection": "Adjunto: rsa.txt"}, note


BUILDERS = {
    "crypto_base64": _t_crypto_base64,
    "crypto_vigenere": _t_crypto_vigenere,
    "crypto_rsa": _t_crypto_rsa,
}
