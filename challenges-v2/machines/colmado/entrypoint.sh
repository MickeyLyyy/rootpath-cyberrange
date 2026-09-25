#!/bin/bash
# Objetivo: escribir la flag en /root/flag.txt (solo root) y arrancar el
# servicio web como el usuario sin privilegios 'player'.
if [ -z "$RP_FLAG" ]; then RP_FLAG="RP{noflag}"; fi
printf '%s' "$RP_FLAG" > /root/flag.txt
chmod 600 /root/flag.txt
exec runuser -u player -- python3 /app/app.py
