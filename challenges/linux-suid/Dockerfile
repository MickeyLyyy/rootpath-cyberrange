FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server sudo gcc libc6-dev procps && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /run/sshd
RUN useradd -m -s /bin/bash player && echo 'player:player' | chpasswd
RUN echo 'RP{su1d_b1n4ry_pr1v3sc}' > /root/flag.txt && chmod 600 /root/flag.txt
COPY readflag.c /tmp/readflag.c
RUN gcc -o /usr/local/bin/readflag /tmp/readflag.c && rm /tmp/readflag.c \
 && chown root:root /usr/local/bin/readflag && chmod 4755 /usr/local/bin/readflag
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
EXPOSE 2222
ENTRYPOINT ["/entrypoint.sh"]
