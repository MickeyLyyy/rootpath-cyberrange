#!/bin/bash
# Caja atacante: terminal web (ttyd) con autenticacion basica.
# El usuario conecta por navegador y dispone de nmap/ssh/curl/socat/...
exec ttyd -p 7681 -c "${TTYD_USER:-player}:${TTYD_PASS:-player}" -W bash
