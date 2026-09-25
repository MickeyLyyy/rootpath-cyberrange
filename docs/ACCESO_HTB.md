# Acceso tipo Hack The Box sobre la red interna (Tailscale)

Objetivo: que el usuario alcance **su** rango (`10.100.<uid>.0/24`) desde **su propia maquina**
(`nmap`, `ssh`, burp...) sin abrir puertos ni VPN propia, usando la red interna (Tailscale).

## Como funciona

```
Usuario (tailnet, 100.x)  --tunel-->  rootpath-gw (host Proxmox)
   --ruta 10.100.0.0/14 via 172.170.10.11-->  LXC 112 (Docker)
   --raw ACCEPT + DOCKER-USER ACCEPT-->  rp-range-u<uid>
        ├── 10.100.<uid>.10  objetivo
        └── 10.100.<uid>.5   caja atacante
```

## Piezas configuradas

1. **Ruta en el host Proxmox** hacia los rangos (persistente, `rootpath-range-route.service`):
   ```
   ip route replace 10.100.0.0/14 via 172.170.10.11
   ```
2. **Anuncio Tailscale** desde `rootpath-gw` (subnet router):
   ```
   tailscale up --advertise-routes=172.170.10.11/32,10.100.0.0/14 \
     --accept-dns=false --snat-subnet-routes=false --accept-routes=false
   ```
3. **LXC: permitir el trafico entrante a los rangos** (`rootpath-expose.service`):
   - `raw PREROUTING` ACCEPT **por delante** de las reglas anti-spoof de Docker
     (`docker` crea `-A PREROUTING -d <ip> ! -i <bridge> -j DROP`):
     ```
     iptables -t raw -I PREROUTING 1 -s 100.64.0.0/10 -d 10.100.0.0/14 -j ACCEPT
     iptables -t raw -I PREROUTING 1 -s 172.170.10.10 -d 10.100.0.0/14 -j ACCEPT
     ```
   - forward:
     ```
     iptables -I DOCKER-USER 1 -i eth0 -d 10.100.0.0/14 -j ACCEPT
     ```
   - `lab_service` reinserta estas reglas al desplegar una maquina (por si Docker reordena).

## Pasos manuales (una sola vez)

1. **Consola Tailscale** → Machines → `rootpath-gw` → **Edit route settings** →
   **aprobar `10.100.0.0/14`**.
2. **Cliente**: activar rutas → `tailscale up --accept-routes`
   (o "Use Tailscale subnets" en la app).
3. **Aislamiento por usuario** (ACL) — requiere una **identidad Tailscale por usuario**:
   ```jsonc
   { "acls": [
       { "action": "accept", "src": ["usuario3@"], "dst": ["10.100.3.0/24:*"] },
       { "action": "accept", "src": ["usuario4@"], "dst": ["10.100.4.0/24:*"] }
   ]}
   ```
   Sin ACL, todos los miembros del tailnet pueden ver todos los rangos.

## Uso por parte del usuario

```bash
# una vez conectado al tailnet con rutas aceptadas
nmap -sV 10.100.<uid>.0/24     # ve objetivo y caja atacante como hosts distintos
ssh ...
```
O bien sigue usando el **terminal web** de la caja atacante (ttyd con auth) que muestra el panel.

## Notas

- `10.100.0.0/14` cubre `10.100.x`–`10.103.x` (uid 0..1023). Para mas rangos, ampliar.
- Docker NO permite alcanzar IPs de contenedor desde fuera por diseno (anti-spoof en
  `raw PREROUTING`); por eso el ACCEPT debe ir **antes** de sus reglas.
- `-sV` funciona; `-sS`/`-O` dependen de que el cliente tenga sockets raw (su Kali si).
