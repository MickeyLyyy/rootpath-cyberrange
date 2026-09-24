# Inventario de recursos creados

## Proxmox
| Recurso | ID | Nombre | Detalle |
|---|---|---|---|
| CT | 112 | rootpath | Debian 12, 4 cores, 8192 MB, 40 GB (local-lvm), unprivileged, nesting=1,keyctl=1 |
| Red | - | vmbr0 | IP estatica 172.170.10.11/24, gw 172.170.10.1 |

## Contenedores Docker (dentro de CT 112)
### Plataforma (compose: rootpath-platform)
| Servicio | Imagen | Puerto host | Uso |
|---|---|---|---|
| ctfd | ctfd/ctfd:latest | 8000 | Panel CTFd |
| db | mariadb:10.11 | interno | Base de datos |
| cache | redis:7-alpine | interno | Cache |

### Retos (compose: rootpath-challenges)
| Reto | Contenedor | Puerto host | Categoria |
|---|---|---|---|
| Comentario Revelador | web-source-comment | 8081 | Web |
| Robots Curiosos | web-robots | 8082 | Web |
| Inclusion Local | web-lfi | 8083 | Web |
| Login Bypass | web-sqli | 8084 | Web |
| Ping Injection | web-cmdi | 8085 | Web |
| SUID Peligroso | linux-suid | 2201 (ssh) | Linux |
| Cron Ajeno | linux-cron | 2202 (ssh) | Linux |
| Capas de Base64 | (estatico) | - | Crypto |
| Cesar Antiguo | (estatico) | - | Crypto |
| Strings Ocultas | (estatico) | - | Forensics |

## Volumenes Docker
rootpath-platform_ctfd-uploads, rootpath-platform_ctfd-db, rootpath-platform_ctfd-cache

## Redes Docker
rootpath (bridge user-defined)
