FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server cron procps && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /run/sshd
RUN useradd -m -s /bin/bash player && echo 'player:player' | chpasswd
RUN echo 'RP{cr0n_j0b_wr1t4bl3}' > /root/flag.txt && chmod 600 /root/flag.txt
RUN printf '#!/bin/bash\n# tarea de backup nocturna (script heredado, permisos laxos)\ntrue\n' > /opt/backup.sh \
 && chmod 777 /opt/backup.sh
RUN echo '* * * * * root /opt/backup.sh' > /etc/cron.d/backup && chmod 644 /etc/cron.d/backup
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
EXPOSE 2222
ENTRYPOINT ["/entrypoint.sh"]
