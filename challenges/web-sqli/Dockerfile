FROM python:3.12-slim
RUN pip install --no-cache-dir flask==3.0.3
WORKDIR /app
COPY app.py /app/app.py
RUN echo 'RP{sqli_0r_1_3qu4ls_1}' > /flag.txt
EXPOSE 5000
CMD ["python","/app/app.py"]
