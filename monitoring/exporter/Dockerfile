FROM python:3.12-slim
RUN pip install --no-cache-dir pymysql==1.1.1
WORKDIR /app
COPY exporter.py /app/exporter.py
EXPOSE 9200
CMD ["python3", "/app/exporter.py"]
