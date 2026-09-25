FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-flask iputils-ping findutils procps \
    && rm -rf /var/lib/apt/lists/*
# Usuario sin privilegios que ejecuta la web + vector de escalada (SUID)
RUN useradd -m -s /bin/bash player && chmod u+s /usr/bin/find
WORKDIR /app
COPY app.py /app/app.py
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]
