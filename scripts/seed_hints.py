from CTFd import create_app
from CTFd.models import db, Challenges, Hints
app = create_app()
app.app_context().push()
H = {
 "Comentario Revelador": [(5,"Mira el codigo fuente HTML de la pagina (Ctrl+U)."),
                          (15,"Los comentarios <!-- --> pueden filtrar informacion."),
                          (30,"La flag esta en un comentario del index.html.")],
 "Robots Curiosos": [(5,"Revisa /robots.txt."),
                     (15,"Los Disallow apuntan a rutas que no quieren indexar."),
                     (30,"Accede a /secret/flag.txt.")],
 "Inclusion Local": [(5,"El parametro page se concatena a una ruta del disco."),
                     (15,"Prueba traversal con ../ para salir del directorio base."),
                     (30,"Hacen falta tres niveles: ?page=../../../flag.txt")],
 "Login Bypass": [(5,"La consulta SQL se construye concatenando tus parametros."),
                  (15,"Cierra la comilla y comenta el resto con -- ."),
                  (30,"Prueba u=admin'-- con cualquier password.")],
 "Ping Injection": [(5,"El servidor ejecuta el comando en una shell."),
                    (15,"Encadena un segundo comando con ; o |"),
                    (30,"host=127.0.0.1; cat /flag.txt")],
 "SUID Peligroso": [(5,"Busca binarios con el bit SUID activado."),
                    (15,"find / -perm -4000 -type f 2>/dev/null"),
                    (30,"Ejecuta /usr/local/bin/readflag.")],
 "Cron Ajeno": [(5,"Un proceso de root ejecuta un script periodicamente."),
                (15,"Revisa /etc/cron.d y los permisos del script."),
                (30,"El script es escribible: anade una linea que copie /root/flag.txt.")],
 "Capas de Base64": [(5,"El contenido esta en Base64."),
                     (15,"Hay que decodificar varias veces."),
                     (30,"Tres veces: base64 -d x3")],
 "Cesar Antiguo": [(5,"Es un cifrado Cesar."),
                   (15,"Prueba todos los desplazamientos (ROT)."),
                   (30,"El desplazamiento es 3.")],
 "Strings Ocultas": [(5,"La flag esta en texto plano dentro del binario."),
                     (15,"Usa la herramienta strings."),
                     (30,"strings evidencia.bin | grep RP{")],
}
for name, hints in H.items():
    c = Challenges.query.filter_by(name=name).first()
    if not c: continue
    Hints.query.filter_by(challenge_id=c.id).delete()
    for cost, text in hints:
        db.session.add(Hints(challenge_id=c.id, content=text, cost=cost))
db.session.commit()
print("HINTS_OK total=%d challenges=%d" % (Hints.query.count(), len(H)))
