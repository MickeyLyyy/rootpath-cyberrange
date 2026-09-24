# RootPath - Fase 5 (Expansion: rutas AD y Blue Team, analiticas)

## Decision de arquitectura
El nodo (1 HDD, 4 cores, 31 GB) no soporta un laboratorio AD Windows/Samba en vivo
(DC + estaciones = 4 GB+ cada una) junto con el resto de la plataforma. Por ello la
ruta AD se implementa con RETOS DE ATAQUE AD deterministas y reales, sin DC en vivo:

- Enumeracion LDAP anonima (LDIF; flag en description base64).
- Ruta a Domain Admin (grafo BloodHound JSON; edge AdminTo).
- Kerberoasting (hash TGS-REP etype 23; cracking RC4-HMAC REAL con wordlist).
- AS-REP Roasting (hash AS-REP 23; cracking RC4-HMAC real).
- Reutilizacion de credenciales (hashes NTLM; cracking MD4 real).

El cracking usa una implementacion propia de MD4 (NTLM) + HMAC-MD5, identica en
esencia al ataque real. El laboratorio AD en vivo queda para hardware dedicado.

## Rutas nuevas (operativas)
- "Pentesting de Active Directory (PNPT)"
  - Enumeracion de Active Directory (2), Ataques a credenciales (2), Movimiento lateral (1)
- "Blue Team (BTL1)"
  - Analisis de logs (2), Forense de red (1), Deteccion y respuesta (vacio, pendiente)
Retos Blue:
- Exfiltracion en logs web (Apache access.log; payload base64).
- Fuerza bruta y persistencia (auth.log; comando sudo post-explotacion).
- Exfiltracion por DNS (dns.log Zeek; reensamblado + base32).

## Puertas de validacion (expansion/build.py)
Cada reto se genera, se resuelve con su solve.sh y se comprueba la flag.
Chequeo NEGATIVO: la flag no debe aparecer en texto plano en el artefacto.

## Analiticas (dashboard del coordinador)
- Endpoint `GET /plugins/rootpath/api/analytics` (auth) -> retos, usuarios, resoluciones,
  pistas usadas, retos mas dificiles (con marca REVISAR), desglose por categoria y top usuarios.
- Pagina CTFd `/analiticas` (menu).

## Evidencia de aceptacion
- 8 retos AD/Blue cargados (cid 16-25) y resueltos por un usuario con exito (`correct`).
- Readiness: AD 100%, Blue Team 67%.
- /rutas muestra ambas rutas con sus dominios y retos.

## Notas
- "Eventos" y "deteccion activa" (SIEM en vivo) quedan como trabajo continuo;
  las analiticas cubren ya la parte de metrica de salud de retos.
- Documentado tambien en /opt/rootpath/docs/FASE5.md.
