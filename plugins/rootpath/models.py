from datetime import datetime

from CTFd.models import db


class RootPathCert(db.Model):
    __tablename__ = "rp_certifications"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text)
    weight = db.Column(db.Float, default=1.0)

class RootPathDomain(db.Model):
    __tablename__ = "rp_domains"
    id = db.Column(db.Integer, primary_key=True)
    cert_id = db.Column(db.Integer, db.ForeignKey("rp_certifications.id", ondelete="CASCADE"))
    name = db.Column(db.String(200))
    weight = db.Column(db.Float, default=1.0)

class RootPathMap(db.Model):
    __tablename__ = "rp_challenge_domains"
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"))
    domain_id = db.Column(db.Integer, db.ForeignKey("rp_domains.id", ondelete="CASCADE"))

class RootPathExam(db.Model):
    __tablename__ = "rp_exam_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    cert_id = db.Column(db.Integer, nullable=True)
    started = db.Column(db.DateTime)
    ends = db.Column(db.DateTime)
    finished = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(32), default="active")
    challenge_ids = db.Column(db.Text)
    report = db.Column(db.LargeBinary(length=2**24), nullable=True)


class RootPathLabAction(db.Model):
    """Auditoria de despliegue/tumba de contenedores de laboratorio.

    Registra, por cada accion del usuario sobre un contenedor de reto, su
    identidad unica (user_id de CTFd) y su IP de origen, para trazabilidad.
    """
    __tablename__ = "rp_lab_actions"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    user_name = db.Column(db.String(128))
    ip = db.Column(db.String(64))
    forwarded_for = db.Column(db.String(255))
    user_agent = db.Column(db.String(255))
    action = db.Column(db.String(16))              # start | stop | restart
    challenge_name = db.Column(db.String(200))
    service = db.Column(db.String(128))
    result = db.Column(db.String(32), index=True)  # ok | error | denied:*
    detail = db.Column(db.Text)

    def as_dict(self):
        return {
            "id": self.id,
            "created_at": (self.created_at.isoformat() + "Z") if self.created_at else None,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "ip": self.ip,
            "forwarded_for": self.forwarded_for,
            "user_agent": self.user_agent,
            "action": self.action,
            "challenge_name": self.challenge_name,
            "service": self.service,
            "result": self.result,
            "detail": self.detail,
        }


class RootPathLabLease(db.Model):
    """Concesion (TTL) de un contenedor de laboratorio compartido (legacy)."""
    __tablename__ = "rp_lab_leases"
    id = db.Column(db.Integer, primary_key=True)
    challenge_name = db.Column(db.String(200), unique=True, nullable=False)
    service = db.Column(db.String(128))
    user_id = db.Column(db.Integer)
    user_name = db.Column(db.String(128))
    started_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, index=True)
    active = db.Column(db.Boolean, default=False, index=True)


class RootPathLabInstance(db.Model):
    """Instancia efimera de laboratorio por usuario (una por reto)."""
    __tablename__ = "rp_lab_instances"
    __table_args__ = (db.UniqueConstraint("user_id", "challenge_id", name="uq_rp_inst_user_chal"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    user_name = db.Column(db.String(128))
    challenge_id = db.Column(db.Integer, index=True)
    challenge_name = db.Column(db.String(200))
    service = db.Column(db.String(128))
    image = db.Column(db.String(160))
    container_name = db.Column(db.String(80))
    host_port = db.Column(db.Integer)
    internal_port = db.Column(db.Integer)
    kind = db.Column(db.String(16))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, index=True)
    status = db.Column(db.String(16), default="running")
