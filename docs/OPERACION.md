# Operacion (runbook)

Todo se ejecuta en el nodo Proxmox como root. Acceso al LXC: `pct exec 112 -- bash`
o `pct enter 112`.

## Arrancar / parar la plataforma
    pct exec 112 -- bash -c 'cd /opt/rootpath && docker compose --env-file .env up -d'
    pct exec 112 -- bash -c 'cd /opt/rootpath && docker compose --env-file .env down'

## Retos
    pct exec 112 -- bash -c 'cd /opt/rootpath/challenges && docker compose up -d'
    pct exec 112 -- bash -c 'cd /opt/rootpath/challenges && docker compose ps'

## Logs
    pct exec 112 -- bash -c 'cd /opt/rootpath && docker compose --env-file .env logs -f ctfd'

## Recargar retos en CTFd (idempotente NO; crea duplicados)
    pct exec 112 -- python3 /opt/rootpath/scripts/load_challenges.py

## Respaldo manual (export completo de CTFd)
    pct exec 112 -- bash -c 'cd /opt/rootpath && docker compose exec -T ctfd flask export_ctf /var/uploads/backup.zip'
    # luego copiar /var/uploads/backup.zip del contenedor ctfd al host

## Reinicio limpio del nodo
Los servicios tienen restart: unless-stopped y el CT 112 tiene onboot=1, por lo que
la plataforma se recupera sola tras un reinicio del nodo.
