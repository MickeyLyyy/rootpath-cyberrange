# Retos Forenses

## `el-analista-desaparecido` (Forensics · EXTREMO · 200)

**Artefacto:** `evidencia.zip` con `captura.pcap` + `disco.img`.

**Cadena de resolución (no se revela en la descripción):**
1. **pcap**: obtener el *hostname* de la víctima (query DNS `analista.corp.local`).
2. **Exfiltración DNS**: reensamblar los subdominios `NN.<chunk>.c2.darknet.do`, decodificar **base32** y aplicar **XOR** con el hostname → contraseña del 7z.
3. **disco.img**: localizar `/srv/backups/secretos.7z` y abrirlo con esa contraseña → `nota.txt` + `foto.jpg`.
4. **nota.txt**: base64 → invertir → passphrase de **steghide**.
5. **foto.jpg**: `steghide extract` → **flag**.
- Distractores: "flag" falsa en un comentario HTTP del pcap y `fake.txt` (base64) en el disco.
- Archivo borrado recuperable: `/home/analista/.bash_history` (carving/`strings`).

**Generación:** `build_extreme.sh` (scapy + mke2fs/debugfs + 7z + steghide + imagemagick).
**Validación:** `solve_extreme.sh` (reproduce la cadena completa y verifica la flag).

**Flag:** `RP{analista_p3rd1d0_dns_7z_st3g0}` (estática).

### Requisitos
```bash
apt-get install -y python3-scapy p7zip-full steghide imagemagick binwalk foremost
```
