#!/bin/bash
# Escribe la flag de runtime y arranca el bus interno + la app
if [ -z "$RP_FLAG" ]; then RP_FLAG="RP{noflag}"; fi
printf '%s' "$RP_FLAG" > /flag.txt
chmod 600 /flag.txt
python3 /app/worker.py &
exec python3 /app/app.py
