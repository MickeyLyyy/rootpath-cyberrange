#!/bin/bash
# NimbusDrive: secretos aleatorios por instancia + arranque
SIGNING_KEY=$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)
INTERNAL_NONCE=$(head -c 16 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20)
INTERNAL_PATH=$(head -c 8 /dev/urandom | od -An -tx1 | tr -d ' \n' | head -c 10)

mkdir -p /app/config /data
cat > /app/config/app.env <<EOF
DB_HOST=ndb-prod-01
SIGNING_KEY=$SIGNING_KEY
INTERNAL_URL=http://127.0.0.1:8080/$INTERNAL_PATH/thumb
INTERNAL_NONCE=$INTERNAL_NONCE
EOF

if [ -z "$RP_FLAG" ]; then RP_FLAG="RP{noflag}"; fi
printf '%s' "$RP_FLAG" > /flag.txt
chmod 600 /flag.txt

export SIGNING_KEY INTERNAL_NONCE INTERNAL_PATH
python3 /app/renderer.py &
exec python3 /app/app.py
