import os
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, abort, session, render_template, redirect
from CTFd.models import db, Challenges, Solves, Hints, HintUnlocks, Users
from CTFd.utils.decorators import authed_only
from CTFd.utils.user import get_current_user
from .models import RootPathCert, RootPathDomain, RootPathMap, RootPathExam

bp = Blueprint(
    "rootpath", __name__,
    url_prefix="/plugins/rootpath",
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)


def _progress(user_id):
    solved = {s.challenge_id for s in Solves.query.filter_by(user_id=user_id).all()}
    hints = {}
    for hu in HintUnlocks.query.filter_by(user_id=user_id).all():
        h = db.session.get(Hints, hu.target)
        if h:
            hints[h.challenge_id] = hints.get(h.challenge_id, 0) + 1
    return solved, hints


def _readiness(solved, hints):
    out = []
    for cert in RootPathCert.query.order_by(RootPathCert.id).all():
        domains = RootPathDomain.query.filter_by(cert_id=cert.id).all()
        acc = 0.0
        totw = 0.0
        dlist = []
        for d in domains:
            maps = RootPathMap.query.filter_by(domain_id=d.id).all()
            cids = [m.challenge_id for m in maps]
            if cids:
                pts = []
                for cid in cids:
                    if cid in solved:
                        pts.append(0.7 if hints.get(cid, 0) > 0 else 1.0)
                    else:
                        pts.append(0.0)
                dscore = sum(pts) / len(pts)
            else:
                dscore = 0.0
            w = d.weight or 1.0
            acc += dscore * w
            totw += w
            dlist.append({"name": d.name, "score": round(dscore * 100), "challenges": len(cids)})
        out.append({
            "id": cert.id, "name": cert.name, "description": cert.description,
            "score": round((acc / totw) * 100) if totw else 0, "domains": dlist,
        })
    return out


@bp.route("/api/ping")
def ping():
    return jsonify({"ok": True, "plugin": "rootpath", "version": "0.2"})


@bp.route("/api/paths")
def paths():
    user = get_current_user()
    solved, hints = _progress(user.id) if user else (set(), {})
    certs = []
    for c in _readiness(solved, hints):
        domains = []
        for d in RootPathDomain.query.filter_by(cert_id=c["id"]).all():
            chs = []
            for m in RootPathMap.query.filter_by(domain_id=d.id).all():
                ch = db.session.get(Challenges, m.challenge_id)
                if not ch:
                    continue
                chs.append({"id": ch.id, "name": ch.name, "category": ch.category,
                            "value": ch.value, "solved": ch.id in solved,
                            "hints_used": hints.get(ch.id, 0)})
            domains.append({"name": d.name, "challenges": chs})
        c["domain_detail"] = domains
        certs.append(c)
    return jsonify({"success": True, "data": certs, "authed": bool(user)})


@bp.route("/api/readiness")
def readiness():
    user = get_current_user()
    solved, hints = _progress(user.id) if user else (set(), {})
    return jsonify({"success": True, "data": _readiness(solved, hints)})


@bp.route("/api/exam/status")
@authed_only
def exam_status():
    u = get_current_user()
    ex = RootPathExam.query.filter_by(user_id=u.id, status="active").order_by(RootPathExam.id.desc()).first()
    if not ex:
        return jsonify({"active": False})
    now = datetime.utcnow()
    if ex.ends and now > ex.ends:
        ex.status = "expired"; db.session.commit()
        return jsonify({"active": False, "expired": True})
    remaining = int((ex.ends - now).total_seconds()) if ex.ends else 0
    cids = [int(x) for x in (ex.challenge_ids or "").split(",") if x]
    solved, _ = _progress(u.id)
    chs = []
    for cid in cids:
        ch = db.session.get(Challenges, cid)
        if ch:
            chs.append({"id": ch.id, "name": ch.name, "category": ch.category, "solved": cid in solved})
    return jsonify({"active": True, "id": ex.id, "remaining": remaining, "challenges": chs,
                    "report_saved": bool(ex.report)})


@bp.route("/api/exam/start", methods=["POST"])
@authed_only
def exam_start():
    u = get_current_user()
    if RootPathExam.query.filter_by(user_id=u.id, status="active").first():
        return jsonify({"success": False, "error": "Ya tienes un examen activo."}), 400
    data = request.get_json() or {}
    cert_id = data.get("cert_id")
    dur = int(data.get("duration_minutes", 180))
    cids = []
    if cert_id:
        for d in RootPathDomain.query.filter_by(cert_id=cert_id).all():
            for m in RootPathMap.query.filter_by(domain_id=d.id).all():
                if m.challenge_id not in cids:
                    cids.append(m.challenge_id)
    else:
        cids = [c.id for c in Challenges.query.order_by(Challenges.id).all()]
    now = datetime.utcnow()
    ex = RootPathExam(user_id=u.id, cert_id=cert_id, started=now,
                      ends=now + timedelta(minutes=dur), status="active",
                      challenge_ids=",".join(map(str, cids)))
    db.session.add(ex); db.session.commit()
    return jsonify({"success": True, "id": ex.id, "challenges": len(cids), "duration_minutes": dur})


@bp.route("/api/exam/report", methods=["POST"])
@authed_only
def exam_report():
    u = get_current_user()
    ex = RootPathExam.query.filter_by(user_id=u.id, status="active").order_by(RootPathExam.id.desc()).first()
    if not ex:
        return jsonify({"success": False, "error": "Sin examen activo."}), 400
    ex.report = ((request.get_json() or {}).get("content", "")).encode("utf-8")
    db.session.commit()
    return jsonify({"success": True})


@bp.route("/api/exam/finish", methods=["POST"])
@authed_only
def exam_finish():
    u = get_current_user()
    ex = RootPathExam.query.filter_by(user_id=u.id, status="active").order_by(RootPathExam.id.desc()).first()
    if not ex:
        return jsonify({"success": False, "error": "Sin examen activo."}), 400
    data = request.get_json() or {}
    if data.get("report"):
        ex.report = data["report"].encode("utf-8")
    ex.finished = datetime.utcnow()
    ex.status = "finished"
    db.session.commit()
    return jsonify({"success": True})


@bp.before_app_request
def _block_hints_during_exam():
    if request.method != "POST":
        return
    p = request.path
    if not (p.startswith("/api/v1/hints") or p.startswith("/api/v1/unlocks")):
        return
    try:
        u = get_current_user()
    except Exception:
        return
    if not u:
        return
    if RootPathExam.query.filter_by(user_id=u.id, status="active").first():
        abort(403, description="Las pistas estan deshabilitadas durante el modo examen.")


# ---------- integracion con agentes (Fase 3) ----------
def _runtime(name, default=None):
    p = "/opt/CTFd/runtime/" + name
    return open(p).read().strip() if os.path.exists(p) else default


@bp.route("/api/status")
def agent_status():
    import json as _json
    paused = _runtime("deploy_paused", "0") == "1"
    ms = _runtime("monitor_status.json")
    try:
        monitor = _json.loads(ms) if ms else None
    except Exception:
        monitor = None
    return jsonify({"success": True, "deploy_paused": paused, "monitor": monitor})


@bp.route("/api/agent/hint")
def agent_hint():
    key = request.headers.get("X-Agent-Key", "")
    expected = _runtime("agent_key")
    if not expected or key != expected:
        abort(403, description="agent key invalida")
    cid = request.args.get("challenge_id", type=int)
    level = request.args.get("level", type=int, default=1)
    hs = Hints.query.filter_by(challenge_id=cid).order_by(Hints.cost).all()
    if not hs:
        return jsonify({"success": False, "error": "sin pistas para el reto"}), 404
    idx = max(1, min(level, len(hs))) - 1
    h = hs[idx]
    return jsonify({"success": True, "challenge_id": cid, "level": idx + 1,
                    "cost": h.cost, "content": h.content})


@bp.before_app_request
def _pause_guard():
    if request.method != "POST":
        return
    if request.path == "/plugins/rootpath/api/exam/start" and _runtime("deploy_paused", "0") == "1":
        abort(503, description="Plataforma en pausa por carga alta (monitor).")


@bp.route("/api/agent/map", methods=["POST"])
def agent_map():
    key = request.headers.get("X-Agent-Key", "")
    if not _runtime("agent_key") or key != _runtime("agent_key"):
        abort(403, description="agent key invalida")
    d = request.get_json() or {}
    ch = Challenges.query.filter_by(name=d.get("challenge_name")).first()
    dom = RootPathDomain.query.filter_by(name=d.get("domain_name")).first()
    if not ch or not dom:
        return jsonify({"success": False, "error": "reto o dominio no encontrado"}), 404
    if not RootPathMap.query.filter_by(challenge_id=ch.id, domain_id=dom.id).first():
        db.session.add(RootPathMap(challenge_id=ch.id, domain_id=dom.id))
        db.session.commit()
    return jsonify({"success": True, "challenge_id": ch.id, "domain_id": dom.id})


@bp.route("/api/analytics")
@authed_only
def analytics():
    chs = Challenges.query.all()
    users = Users.query.count()
    solves = Solves.query.all()
    per = {}
    for s in solves:
        per[s.challenge_id] = per.get(s.challenge_id, 0) + 1
    val = {c.id: c.value for c in chs}
    rows = []
    for c in chs:
        sc = per.get(c.id, 0)
        rate = round(100.0 * sc / max(1, users), 1)
        rows.append({"id": c.id, "name": c.name, "category": c.category, "value": c.value,
                     "solves": sc, "solve_rate": rate, "flag": (rate < 10.0 and users > 1)})
    hardest = sorted(rows, key=lambda r: r["solve_rate"])[:12]
    cats = {}
    for r in rows:
        cc = cats.setdefault(r["category"], {"category": r["category"], "challenges": 0, "solves": 0})
        cc["challenges"] += 1; cc["solves"] += r["solves"]
    bycat = sorted(cats.values(), key=lambda x: -x["solves"])
    uscore = {}
    for s in solves:
        uscore[s.user_id] = uscore.get(s.user_id, 0) + val.get(s.challenge_id, 0)
    unames = {u.id: u.name for u in Users.query.all()}
    top = [{"user": unames.get(uid, "?"), "score": sc} for uid, sc in sorted(uscore.items(), key=lambda x: -x[1])[:10]]
    return jsonify({"success": True, "data": {
        "challenges": len(chs), "users": users, "solves": len(solves),
        "hint_unlocks": HintUnlocks.query.count(),
        "hardest": hardest, "by_category": bycat, "top_users": top}})


@bp.route("/dashboard")
@authed_only
def dashboard():
    return render_template("dashboard.html", nonce=session.get("nonce", ""))


@bp.route("/api/catalog")
@authed_only
def catalog_api():
    u = get_current_user()
    solved = {x.challenge_id for x in Solves.query.filter_by(user_id=u.id).all()}
    unlocked = {hu.target for hu in HintUnlocks.query.filter_by(user_id=u.id).all()}
    out = []
    for c in Challenges.query.order_by(Challenges.id).all():
        hs = Hints.query.filter_by(challenge_id=c.id).order_by(Hints.cost).all()
        hints = [{"id": h.id, "cost": h.cost, "content": (h.content if h.id in unlocked else None)} for h in hs]
        out.append({"id": c.id, "name": c.name, "category": c.category, "value": c.value,
                    "description": c.description, "solved": c.id in solved, "hints": hints})
    return jsonify({"success": True, "data": out})


# ---------- laboratorios (control real) ----------
LAB_URL = "http://172.170.10.11:9001"


def _lab_request(path, method="GET", payload=None):
    import requests as _rq
    key = _runtime("agent_key", "")
    h = {"X-Agent-Key": key}
    if method == "GET":
        r = _rq.get(LAB_URL + path, headers=h, params=payload or {}, timeout=15)
    else:
        r = _rq.post(LAB_URL + path, headers=dict(h, **{"Content-Type": "application/json"}),
                     json=payload or {}, timeout=180)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"error": r.text[:200]}


@bp.route("/api/lab/status")
@authed_only
def lab_status():
    code, data = _lab_request("/lab/status", "GET", {"name": request.args.get("name", "")})
    return jsonify(data), code


@bp.route("/api/lab/control", methods=["POST"])
@authed_only
def lab_control():
    d = request.get_json() or {}
    action = d.get("action")
    if action not in ("start", "stop", "restart"):
        return jsonify({"success": False, "error": "accion invalida"}), 400
    code, data = _lab_request("/lab/" + action, "POST", {"name": d.get("name")})
    return jsonify(data), code


HIDE_PREFIXES = ("/challenges", "/scoreboard", "/users", "/teams", "/team/",
                 "/notifications", "/settings", "/awards", "/rules", "/register",
                 "/pages/", "/page/", "/solutions", "/hints", "/dynamic_challenges",
                 "/brackets", "/confirm", "/reset", "/edit", "/profile")
SAFE_PREFIXES = ("/api/", "/plugins/", "/themes/", "/static/", "/files/", "/admin",
                 "/login", "/logout", "/setup", "/favicon")


def _redir():
    u = get_current_user()
    return redirect("/plugins/rootpath/dashboard" if u else "/login")


@bp.before_app_request
def _hide_ctfd():
    if request.method != "GET":
        return
    p = request.path
    if p == "/":
        return _redir()
    for safe in SAFE_PREFIXES:
        if p.startswith(safe):
            return
    for pre in HIDE_PREFIXES:
        if p.startswith(pre):
            return _redir()
