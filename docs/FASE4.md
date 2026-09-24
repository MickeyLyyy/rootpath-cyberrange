# RootPath - Fase 4 (Agente creador: pipeline creador -> validador -> aprobacion)

Sin GPU/LLM disponible, el "creador" es un generador determinista y parametrizado que
compone retos REALES desde plantillas verificadas (con flag aleatoria). El flujo es:

    creador(genera) -> validador(construye y resuelve en entorno desechable) -> humano(aprueba) -> publicar

## Agentes (allowlist en agents/bus.py)
- creador  : generate_challenge, list_staging
- validador: validate_challenge
- mentor   : approve_challenge, reject_challenge, publish_challenge   (humano en el bucle)
Toda accion queda en la auditoria encadenada (agents/audit.jsonl).

## Estado (pipeline/pipeline.json)
draft -> validated -> approved -> published

## Plantillas (pipeline/templates.py)
- linux_suid       -> SSH + binario SUID que lee /root/flag.txt (flag 600, no legible sin escalar)
- web_idor         -> Flask: /user/<id>; la flag esta en el id 0
- web_cmdi         -> Flask: utilidad DNS con inyeccion de comandos (; cat /flag.txt)
- web_lfi          -> Flask: visor con path traversal (../../../flag.txt)
- crypto_vigenere  -> adjunto cifrado con Vigenere (clave conocida)

## Puertas del validador (autom??ticas)
1. docker build de la imagen del reto.
2. arranque en red desechable `rp-pipe-test`.
3. ESPERA por readiness real (HTTP 200 / banner SSH), no solo puerto abierto.
4. ejecuta solve.sh y comprueba que obtiene la flag.
5. comprobaciones NEGATIVAS (que no se resuelva trivialmente):
   - SUID: /root/flag.txt en 600 y NO legible por el usuario.
   - IDOR/CMDi/LFI: la flag no aparece sin explotar.
   - Vigenere: no esta en texto plano en el adjunto.
6. Si todo pasa -> estado `validated`.

## Publicacion (pipeline/publisher.py)
- Los retos de servicio se anaden a `pipeline/published-compose.yml` y se levantan.
- Se cargan en CTFd (reto + flag + 3 pistas); los estaticos suben su adjunto.
- Se mapean al dominio de certificacion via el endpoint interno `/plugins/rootpath/api/agent/map`
  (protegido por X-Agent-Key), de modo que aparecen en /rutas.

## Comandos
    # agente creador (allowlist + auditoria)
    python3 agents/cli.py creador generate_challenge '{"title":"...","template":"web_lfi","category":"Web","value":100,"cert":"...","domain":"..."}'
    python3 agents/cli.py list_staging
    python3 agents/cli.py validador validate_challenge '{"slug":"mi-reto"}'
    # aprobacion HUMANA
    python3 agents/cli.py mentor approve_challenge '{"slug":"mi-reto","by":"mentor"}'
    python3 agents/cli.py mentor publish_challenge '{"slug":"mi-reto"}'
    # pipeline completo de ejemplo
    python3 pipeline/run_pipeline.py

## Evidencia de aceptacion (5 retos publicados por el pipeline)
| slug | cid | tipo | estado |
|---|---|---|---|
| cifrado-vigenere | 11 | estatico | published |
| panel-de-perfiles | 12 | web (IDOR) | published |
| diagnostico-de-red | 13 | web (CMDi) | published |
| visor-de-documentos | 14 | web (LFI) | published |
| auditoria-suid | 15 | linux (SUID) | published |

- Los 5 resueltos por solve.sh desde el propio entorno (solve_ok=True).
- Mapeados a dominios eJPT y Security+ (visibles en /rutas).
- Auditoria encadenada verificada (cadena_valida=True).

## Notas
- El creador NO es un LLM; es determinista y reproducible. Sustituirlo por un LLM en el futuro
  no cambia el pipeline (solo el paso de generacion).
- La aprobacion es siempre humana (mentor): el validador nunca publica solo.
