FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        nmap netcat-openbsd curl ca-certificates wget python3 socat openssh-client \
        iputils-ping dnsutils less procps vim-tiny \
    && rm -rf /var/lib/apt/lists/*
# ttyd (terminal web) desde binario estatico oficial
RUN curl -fsSL -o /usr/local/bin/ttyd \
        https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 \
    && chmod +x /usr/local/bin/ttyd
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 7681
ENTRYPOINT ["/entrypoint.sh"]
