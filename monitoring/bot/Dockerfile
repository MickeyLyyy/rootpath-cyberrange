FROM python:3.12-slim
RUN pip install --no-cache-dir requests==2.32.3 pymysql==1.1.1
WORKDIR /app
COPY bot.py /app/bot.py
CMD ["python3", "/app/bot.py"]
