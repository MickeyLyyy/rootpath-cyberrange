FROM python:3.12-slim
RUN pip install --no-cache-dir flask==3.0.3 requests==2.32.3
WORKDIR /app
COPY app.py renderer.py /app/
COPY entrypoint.sh /entrypoint.sh
COPY static /app/static
COPY templates /app/templates
RUN chmod +x /entrypoint.sh
EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
