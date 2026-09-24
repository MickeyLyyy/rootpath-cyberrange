FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir flask==3.0.3
WORKDIR /app
COPY app.py /app/app.py
RUN echo 'RP{cmd_1nj3ct10n_pwn3d}' > /flag.txt
EXPOSE 5000
CMD ["python","/app/app.py"]
