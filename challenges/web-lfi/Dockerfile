FROM python:3.12-slim
RUN pip install --no-cache-dir flask==3.0.3
WORKDIR /app
COPY app.py /app/app.py
RUN mkdir -p /var/www/pages && echo '<p>Pagina de inicio. Prueba ?page=home</p>' > /var/www/pages/home
RUN echo 'RP{lfi_p4th_tr4v3rs4l}' > /flag.txt
EXPOSE 5000
CMD ["python","/app/app.py"]
