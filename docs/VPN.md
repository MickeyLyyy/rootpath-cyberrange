# VPN — Acceso remoto (solo RootPath)

Objetivo: que clientes externos lleguen **solo** al contenedor RootPath (`172.170.10.11`),
no al host Proxmox (`172.170.10.10`) ni al resto de la LAN.

## Opción A — Tailscale (recomendada)
1. Instalar en el host Proxmox:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   systemctl enable --now tailscaled
   ```
2. Levantar el nodo (subnet router), **sin SNAT** (preserva la IP real del cliente):
   ```bash
   tailscale up --hostname=rootpath-gw \
     --advertise-routes=172.170.10.11/32 \
     --accept-dns=false --snat-subnet-routes=false --accept-routes=false
   ```
3. En la consola: **Machines → rootpath-gw → Edit route settings → aprobar `172.170.10.11/32`**.
4. ACL (JSON editor) para que los miembros lleguen al contenedor:
   ```json
   { "acls": [ { "action": "accept", "src": ["autogroup:member"], "dst": ["172.170.10.11:*"] } ] }
   ```
5. Cliente: instalar Tailscale, iniciar sesión en el **mismo tailnet** y activar
   **“Use Tailscale subnets”** (`tailscale up --accept-routes`).
6. Probar: `ping 172.170.10.11` y `http://172.170.10.11:8000`.

**Ruta de retorno en el LXC** (necesaria sin SNAT):
```bash
# /etc/network/interfaces (dentro del LXC 112)
post-up ip route add 100.64.0.0/10 via 172.170.10.10 || true
```
> El rango `100.64.0.0/10` es el de las IPs Tailscale.

## Opción B — WireGuard (en el host)
1. `apt-get install -y wireguard-tools` (crear `/etc/wireguard`).
2. Claves y `/etc/wireguard/wg0.conf`:
   ```
   [Interface]
   Address = 10.13.13.1/24
   ListenPort = 51820
   PrivateKey = <server.key>
   PostUp   = iptables -A FORWARD -i wg0 -o vmbr0 -d 172.170.10.11/32 -j ACCEPT
   PostUp   = iptables -A FORWARD -i vmbr0 -o wg0 -s 172.170.10.11/32 -j ACCEPT
   PostUp   = iptables -A FORWARD -i wg0 ! -d 172.170.10.11/32 -j DROP
   ```
3. Cliente `rootpath.conf` (túnel dividido):
   ```
   [Interface]
   PrivateKey = <client.key>
   Address = 10.13.13.2/32
   [Peer]
   PublicKey = <server.pub>
   Endpoint = 74.244.193.132:51820
   AllowedIPs = 172.170.10.11/32
   PersistentKeepalive = 25
   ```
4. **Ruta de retorno en el LXC**: `10.13.13.0/24 via 172.170.10.10`.
5. Para acceso desde Internet: **port-forward en el MikroTik** UDP 51820 → 172.170.10.10.

## Diferencias
| | Tailscale | WireGuard |
|---|---|---|
| Cuenta | Sí (login) | No |
| Port-forward router | No (NAT traversal) | Sí (UDP 51820) |
| Gestión usuarios | Consola Tailscale | Claves por cliente |
| Restricción a RootPath | Ruta `/32` + ACL | Regla FORWARD `DROP` |

## Restricción efectiva a RootPath
- **Cliente**: `AllowedIPs = 172.170.10.11/32` (solo eso va por el túnel).
- **Servidor**: firewall que **solo** permite reenviar hacia `172.170.10.11`; el resto se descarta.
