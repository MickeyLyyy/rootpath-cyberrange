from CTFd import create_app
from CTFd.models import db, Challenges
from CTFd.plugins.rootpath.models import RootPathCert, RootPathDomain, RootPathMap

app = create_app()
with app.app_context():
    RootPathMap.query.delete()
    RootPathDomain.query.delete()
    RootPathCert.query.delete()
    db.session.commit()

    def cid(n):
        c = Challenges.query.filter_by(name=n).first()
        return c.id if c else None

    seed = {
     "Fundamentos de Pentesting (eJPT)": (
        "Ruta de entrada: reconocimiento, web, explotacion Linux y cripto/forense.",
        [("Reconocimiento y Web", 1.0,
          ["Comentario Revelador","Robots Curiosos","Inclusion Local","Login Bypass","Ping Injection"]),
         ("Explotacion de Sistemas Linux", 1.0, ["SUID Peligroso","Cron Ajeno"]),
         ("Criptografia y Forense", 0.5, ["Capas de Base64","Cesar Antiguo","Strings Ocultas"])]),
     "Pentesting Intermedio (PNPT)": (
        "Ruta intermedia: web avanzada, post-explotacion y Active Directory.",
        [("Explotacion Web Avanzada", 1.0, ["Login Bypass","Inclusion Local","Ping Injection"]),
         ("Post-explotacion Linux", 1.0, ["SUID Peligroso","Cron Ajeno"]),
         ("Active Directory / Movimiento Lateral", 1.5, [])]),
     "Seguridad General (Security+)": (
        "Conceptos: criptografia, forense y seguridad web.",
        [("Criptografia", 1.0, ["Capas de Base64","Cesar Antiguo"]),
         ("Forense", 1.0, ["Strings Ocultas"]),
         ("Seguridad Web", 1.0,
          ["Comentario Revelador","Robots Curiosos","Inclusion Local","Login Bypass","Ping Injection"])]),
    }

    for cname, (desc, domains) in seed.items():
        c = RootPathCert(name=cname, description=desc, weight=1.0)
        db.session.add(c); db.session.flush()
        for dname, w, chs in domains:
            d = RootPathDomain(cert_id=c.id, name=dname, weight=w)
            db.session.add(d); db.session.flush()
            for chn in chs:
                x = cid(chn)
                if x:
                    db.session.add(RootPathMap(challenge_id=x, domain_id=d.id))
    db.session.commit()
    print("SEED_OK certs=%d domains=%d map=%d" % (
        RootPathCert.query.count(), RootPathDomain.query.count(), RootPathMap.query.count()))
