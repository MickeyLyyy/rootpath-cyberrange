from CTFd import create_app
from CTFd.models import db, Challenges
from CTFd.plugins.rootpath.models import RootPathCert, RootPathDomain, RootPathMap

app = create_app(); app.app_context().push()

certs = {
 "Pentesting de Active Directory (PNPT)": (
   "Ruta AD: enumeracion, ataques a credenciales y movimiento lateral.",
   [("Enumeracion de Active Directory", 1.0, ["Enumeracion LDAP anonima", "Ruta a Domain Admin"]),
    ("Ataques a credenciales", 1.0, ["Kerberoasting", "AS-REP Roasting"]),
    ("Movimiento lateral", 1.0, ["Reutilizacion de credenciales"])]),
 "Blue Team (BTL1)": (
   "Ruta defensiva: analisis de logs y forense de red.",
   [("Analisis de logs", 1.0, ["Exfiltracion en logs web", "Fuerza bruta y persistencia"]),
    ("Forense de red", 1.0, ["Exfiltracion por DNS"]),
    ("Deteccion y respuesta", 1.0, [])]),
}
for cname, (desc, domains) in certs.items():
    c = RootPathCert.query.filter_by(name=cname).first()
    if not c:
        c = RootPathCert(name=cname, description=desc, weight=1.0); db.session.add(c); db.session.flush()
    for dname, w, chs in domains:
        d = RootPathDomain.query.filter_by(cert_id=c.id, name=dname).first()
        if not d:
            d = RootPathDomain(cert_id=c.id, name=dname, weight=w); db.session.add(d); db.session.flush()
        for chn in chs:
            ch = Challenges.query.filter_by(name=chn).first()
            if ch and not RootPathMap.query.filter_by(challenge_id=ch.id, domain_id=d.id).first():
                db.session.add(RootPathMap(challenge_id=ch.id, domain_id=d.id))
db.session.commit()
print("EXPANSION_SEED_OK certs=%d domains=%d map=%d" % (
    RootPathCert.query.count(), RootPathDomain.query.count(), RootPathMap.query.count()))
