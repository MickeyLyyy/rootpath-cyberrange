#!/bin/bash
if [ -z "$RP_FLAG" ]; then RP_FLAG="RP{noflag}"; fi
printf '%s' "$RP_FLAG" > /flag.txt
chmod 600 /flag.txt
exec python3 /app/app.py
