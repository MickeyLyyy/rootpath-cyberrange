#!/bin/bash
# Escribe la flag de runtime y arranca el bus interno + la app
printf '%s' "${RP_FLAG:-RP{noflag}}" > /flag.txt
chmod 600 /flag.txt
python3 /app/worker.py &
exec python3 /app/app.py
