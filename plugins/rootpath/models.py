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
