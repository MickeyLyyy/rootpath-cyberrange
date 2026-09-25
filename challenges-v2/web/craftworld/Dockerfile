FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir flask==3.0.3
WORKDIR /app
COPY app.py /app/
COPY entrypoint.sh /entrypoint.sh
COPY static /app/static
COPY templates /app/templates
RUN chmod +x /entrypoint.sh
EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
