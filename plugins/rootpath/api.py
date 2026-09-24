import os
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, abort, session, render_template, redirect
from CTFd.models import (db, Challenges, Solves, Hints, HintUnlocks, Users, ChallengeFiles,
                         Pages, UserFields, Submissions, Tracking)
from CTFd.utils.decorators import authed_only, admins_only
from CTFd.utils.user import get_current_user, is_admin
from .models import (RootPathCert, RootPathDomain, RootPathMap, RootPathExam,
                     RootPathLabAction, RootPathLabLease, RootPathLabInstance)
from .flags import user_flag

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


@bp.route("/api/me")
@authed_only
def me_api():
    """Identidad + rol del usuario (CTFd no expone 'type' en /api/v1/users/me)."""
    u = get_current_user()
    return jsonify({"success": True, "admin": bool(is_admin()),
                    "id": u.id, "name": u.name, "email": u.email})


@bp.route("/admin")
@admins_only
def admin_panel():
    """Panel administrativo RootPath (solo admins)."""
    return render_template("admin.html")


@bp.route("/api/admin/overview")
@admins_only
def admin_overview():
    """Datos agregados para el panel administrativo."""
    users = Users.query.order_by(Users.id).all()
    chs = Challenges.query.order_by(Challenges.id).all()
    solves = Solves.query.all()
    subs = Submissions.query.order_by(Submissions.id.desc()).limit(200).all()

    val = {c.id: c.value for c in chs}
    cat_of = {c.id: c.category for c in chs}
    per_ch = {}
    uscore = {}
    solved_by = {}
    for s in solves:
        per_ch[s.challenge_id] = per_ch.get(s.challenge_id, 0) + 1
        uscore[s.user_id] = uscore.get(s.user_id, 0) + val.get(s.challenge_id, 0)
        solved_by.setdefault(s.user_id, set()).add(s.challenge_id)

    ipmap = {}
    all_ips = set()
    for t in Tracking.query.all():
        if t.ip:
            all_ips.add(t.ip)
        if t.user_id:
            ipmap.setdefault(t.user_id, set()).add(t.ip)

    cat_names = sorted({c.category for c in chs if c.category})
    cats = {}
    for c in chs:
        e = cats.setdefault(c.category, {"category": c.category, "challenges": 0, "solves": 0})
        e["challenges"] += 1
        e["solves"] += per_ch.get(c.id, 0)
    bycat = sorted(cats.values(), key=lambda x: -x["solves"])
    cat_max = max([e["solves"] for e in bycat] or [1]) or 1

    users_out = [{"id": u.id, "name": u.name, "email": u.email,
                  "type": (u.type or "user"), "points": uscore.get(u.id, 0),
                  "ips": len(ipmap.get(u.id, ())), "verified": bool(u.verified),
                  "banned": bool(u.banned), "hidden": bool(u.hidden)} for u in users]

    scoreboard = sorted([{"id": u.id, "user": u.name, "points": uscore.get(u.id, 0),
                          "solved": len(solved_by.get(u.id, ()))} for u in users],
                        key=lambda x: -x["points"])

    chs_out = [{"id": c.id, "name": c.name, "category": c.category, "value": c.value,
                "state": c.state, "solves": per_ch.get(c.id, 0)} for c in chs]

    uname = {u.id: u.name for u in users}
    cname = {c.id: c.name for c in chs}
    subs_out = [{"id": s.id, "user": uname.get(s.user_id, "?"),
                 "challenge": cname.get(s.challenge_id, "?"), "type": s.type,
                 "ip": s.ip, "provided": (s.provided or "")[:60],
                 "date": (s.date.isoformat() + "Z") if s.date else None} for s in subs]

    matrix_rows = []
    for u in users:
        solved_cids = solved_by.get(u.id, set())
        matrix_rows.append({"user": u.name,
                            "cells": [sum(1 for cid in solved_cids if cat_of.get(cid) == cat)
                                      for cat in cat_names]})

    total_points = sum(uscore.values())
    return jsonify({"success": True, "data": {
        "stats": {"users": len(users), "ips": len(all_ips), "points": total_points,
                  "challenges": len(chs), "solves": len(solves),
                  "submissions": Submissions.query.count(),
                  "correct": Submissions.query.filter_by(type="correct").count(),
                  "incorrect": Submissions.query.filter_by(type="incorrect").count()},
        "categories": bycat, "cat_max": cat_max,
        "users": users_out, "challenges": chs_out,
        "scoreboard": scoreboard, "submissions": subs_out,
        "matrix": {"categories": cat_names, "rows": matrix_rows},
    }})


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
        files = [{"name": os.path.basename(f.location), "url": "/files/" + f.location}
                 for f in ChallengeFiles.query.filter_by(challenge_id=c.id).all()]
        out.append({"id": c.id, "name": c.name, "category": c.category, "value": c.value,
                    "description": c.description, "solved": c.id in solved, "hints": hints,
                    "files": files})
    return jsonify({"success": True, "data": out})


# ---------- laboratorios: instancias efimeras por usuario ----------
LAB_URL = "http://172.170.10.11:9001"
LAB_HOST = "172.170.10.11"
LAB_ACTIONS = ("start", "stop", "restart")
LAB_RATE_LIMIT = 30     # acciones por usuario
LAB_RATE_WINDOW = 60    # ventana en segundos
LAB_DEFAULT_TTL_MINUTES = 60
LAB_PORT_MIN = 30000
LAB_PORT_MAX = 40000
LAB_MAX_PER_USER = 3    # instancias simultaneas por usuario


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


def _client_ip():
    """IP de origen del cliente. Prefiere X-Forwarded-For (detras de proxy)."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()[:64]
    xri = request.headers.get("X-Real-IP", "").strip()
    if xri:
        return xri[:64]
    return (request.remote_addr or "?")[:64]


def _log_lab_action(user, action, name, result, service=None, detail=None):
    row = RootPathLabAction(
        user_id=int(user.id),
        user_name=(user.name or "")[:128],
        ip=_client_ip(),
        forwarded_for=(request.headers.get("X-Forwarded-For", "") or "")[:255] or None,
        user_agent=(request.headers.get("User-Agent", "") or "")[:255] or None,
        action=str(action or "")[:16],
        challenge_name=(name or "")[:200] or None,
        service=(service or "")[:128] or None,
        result=str(result or "")[:32],
        detail=detail,
    )
    db.session.add(row)
    db.session.commit()
    return row


def _lab_recent_count(user_id):
    since = datetime.utcnow() - timedelta(seconds=LAB_RATE_WINDOW)
    return RootPathLabAction.query.filter(
        RootPathLabAction.user_id == user_id,
        RootPathLabAction.created_at >= since,
        ~RootPathLabAction.result.like("ok:auto%"),
    ).count()


def _lab_ttl_minutes():
    raw = (_runtime("lab_ttl_minutes", str(LAB_DEFAULT_TTL_MINUTES)) or str(LAB_DEFAULT_TTL_MINUTES)).strip()
    try:
        n = int(raw)
        return n if n > 0 else LAB_DEFAULT_TTL_MINUTES
    except ValueError:
        return LAB_DEFAULT_TTL_MINUTES


def _lab_map():
    """Allowlist de retos con servicio (compartida con el lab_service)."""
    import json as _json
    try:
        with open("/opt/CTFd/runtime/lab_map.json", encoding="utf-8") as fh:
            return _json.load(fh)
    except Exception:
        return {}


def _lab_meta(name):
    return _lab_map().get(name)


def _alloc_port(used):
    for p in range(LAB_PORT_MIN, LAB_PORT_MAX + 1):
        if p not in used:
            return p
    return None


def _instance_conn(inst):
    """Cadena de conexion que se muestra al usuario para su instancia."""
    if not inst:
        return None
    if inst.kind == "linux":
        meta = _lab_meta(inst.challenge_name) or {}
        return "ssh %s@%s -p %d   (password: %s)" % (
            meta.get("ssh_user", "player"), LAB_HOST, inst.host_port,
            meta.get("ssh_pass", "player"))
    return "http://%s:%d/" % (LAB_HOST, inst.host_port)


def _log_lab_action_sys(name, user_id, user_name, service, action, result, detail=None, ip="reaper"):
    row = RootPathLabAction(
        user_id=user_id or 0,
        user_name=(user_name or "auto")[:128],
        ip=ip,
        user_agent="rootpath-reaper",
        action=action,
        challenge_name=(name or "")[:200] or None,
        service=(service or "")[:128] or None,
        result=str(result or "")[:32],
        detail=detail,
    )
    db.session.add(row)
    db.session.commit()
    return row


@bp.after_app_request
def _close_on_solve(response):
    """Al acertar la flag, destruye la instancia de ESE usuario para el reto."""
    try:
        if request.method != "POST" or request.path != "/api/v1/challenges/attempt":
            return response
        try:
            payload = response.get_json(silent=True)
        except Exception:
            payload = None
        if not payload or not payload.get("success"):
            return response
        status = (payload.get("data") or {}).get("status")
        if status not in ("correct", "already_solved"):
            return response
        body = request.get_json(silent=True) or {}
        cid = body.get("challenge_id")
        ch = db.session.get(Challenges, int(cid)) if cid is not None else None
        user = get_current_user()
        if not ch or not user:
            return response
        inst = RootPathLabInstance.query.filter_by(user_id=user.id, challenge_id=ch.id).first()
        if not inst:
            return response
        code, data = _lab_request("/lab/destroy", "POST",
                                  {"name": ch.name, "uid": user.id, "container": inst.container_name})
        _log_lab_action(user, "stop", ch.name,
                        "ok:auto_solve" if code == 200 else "error:%s" % code,
                        service=inst.service)
        db.session.delete(inst)
        db.session.commit()
    except Exception:
        pass
    return response


@bp.route("/api/lab/status")
@authed_only
def lab_status():
    """Estado de la instancia del usuario actual para un reto."""
    user = get_current_user()
    name = request.args.get("name", "")
    meta = _lab_meta(name)
    out = {"success": True, "name": name, "configured": bool(meta),
           "ttl_minutes": _lab_ttl_minutes(), "running": False, "deployed": False, "remaining": 0}
    if meta:
        out["kind"] = meta.get("kind")
    ch = Challenges.query.filter_by(name=name).first()
    inst = None
    if ch:
        inst = RootPathLabInstance.query.filter_by(user_id=user.id, challenge_id=ch.id).first()
    if inst:
        out["deployed"] = True
        out["host_port"] = inst.host_port
        out["service"] = inst.service
        out["container"] = inst.container_name
        out["connection"] = _instance_conn(inst)
        code, data = _lab_request("/lab/status", "GET", {"name": name, "uid": user.id})
        if code == 200 and isinstance(data, dict):
            out["running"] = bool(data.get("running"))
        now = datetime.utcnow()
        if out["running"] and inst.expires_at:
            out["expires_at"] = inst.expires_at.isoformat() + "Z"
            out["remaining"] = max(0, int((inst.expires_at - now).total_seconds()))
        elif not out["running"]:
            # instancia registrada pero no viva -> limpiar
            db.session.delete(inst)
            db.session.commit()
            out["deployed"] = False
            out["connection"] = None
    return jsonify(out)


@bp.route("/api/lab/control", methods=["POST"])
@authed_only
def lab_control():
    """Deploy/destroy de la instancia del usuario (por reto)."""
    user = get_current_user()
    d = request.get_json() or {}
    action = d.get("action")
    name = (d.get("name") or "").strip()
    if action not in LAB_ACTIONS:
        _log_lab_action(user, action, name, "denied:bad_action")
        return jsonify({"success": False, "error": "accion invalida"}), 400
    if not name:
        _log_lab_action(user, action, "", "denied:no_name")
        return jsonify({"success": False, "error": "reto no indicado"}), 400
    meta = _lab_meta(name)
    if not meta:
        _log_lab_action(user, action, name, "denied:no_service")
        return jsonify({"success": False, "error": "Este reto no tiene servicio desplegable"}), 400
    if not is_admin() and _lab_recent_count(user.id) >= LAB_RATE_LIMIT:
        _log_lab_action(user, action, name, "denied:rate_limit")
        return jsonify({"success": False, "error": "demasiadas acciones, espera un momento"}), 429

    ch = Challenges.query.filter_by(name=name).first()
    cid = ch.id if ch else None
    inst = RootPathLabInstance.query.filter_by(user_id=user.id, challenge_id=cid).first() if cid else None

    if action == "stop":
        code, data = _lab_request("/lab/destroy", "POST",
                                  {"name": name, "uid": user.id,
                                   "container": (inst.container_name if inst else None)})
        if inst:
            db.session.delete(inst)
            db.session.commit()
        _log_lab_action(user, "stop", name, "ok" if code == 200 else "error:%s" % code,
                        service=meta.get("service"))
        return jsonify({"success": code == 200, "action": "stop"}), (200 if code == 200 else code)

    # start / restart: borra la instancia previa y despliega una nueva
    if inst:
        _lab_request("/lab/destroy", "POST",
                     {"name": name, "uid": user.id, "container": inst.container_name})
        db.session.delete(inst)
        db.session.commit()

    active = RootPathLabInstance.query.filter_by(user_id=user.id).count()
    if active >= LAB_MAX_PER_USER and not is_admin():
        _log_lab_action(user, action, name, "denied:max_instances")
        return jsonify({"success": False,
                        "error": "Limite de %d instancias activas. Cierra alguna primero." % LAB_MAX_PER_USER}), 429

    used = {r.host_port for r in RootPathLabInstance.query.all() if r.host_port}
    port = _alloc_port(used)
    if not port:
        _log_lab_action(user, action, name, "error:no_port")
        return jsonify({"success": False, "error": "sin puertos libres"}), 503

    code, data = _lab_request("/lab/deploy", "POST",
                              {"name": name, "uid": user.id, "host_port": port,
                               "flag": user_flag(user.id, cid, meta.get("service"))})
    ok = bool(isinstance(data, dict) and data.get("ok"))
    if not ok:
        _log_lab_action(user, action, name, "error:%s" % code,
                        detail=((data.get("out") or data.get("error") or "")[:1000]
                                if isinstance(data, dict) else None) or None)
        return jsonify({"success": False, "error": "no se pudo desplegar el laboratorio",
                        "detail": data}), 500

    now = datetime.utcnow()
    inst = RootPathLabInstance(
        user_id=user.id, user_name=(user.name or "")[:128],
        challenge_id=cid, challenge_name=name, service=meta.get("service"),
        image=meta.get("image"), container_name=data.get("container"),
        host_port=port, internal_port=meta.get("internal_port"), kind=meta.get("kind"),
        created_at=now, expires_at=now + timedelta(minutes=_lab_ttl_minutes()), status="running")
    db.session.add(inst)
    db.session.commit()
    _log_lab_action(user, action, name, "ok", service=meta.get("service"))
    return jsonify({"success": True, "action": action, "host_port": port,
                    "container": inst.container_name, "connection": _instance_conn(inst),
                    "remaining": _lab_ttl_minutes() * 60})


@bp.route("/api/agent/reap", methods=["GET", "POST"])
def agent_reap():
    """Destruye las instancias cuyo TTL expiro. Lo invoca el reaper local."""
    key = request.headers.get("X-Agent-Key", "")
    if not _runtime("agent_key") or key != _runtime("agent_key"):
        abort(403, description="agent key invalida")
    now = datetime.utcnow()
    expired = RootPathLabInstance.query.filter(
        RootPathLabInstance.expires_at.isnot(None),
        RootPathLabInstance.expires_at <= now,
    ).all()
    reaped = []
    for inst in expired:
        code, data = _lab_request("/lab/destroy", "POST",
                                  {"name": inst.challenge_name, "uid": inst.user_id,
                                   "container": inst.container_name})
        ok = code == 200
        _log_lab_action_sys(inst.challenge_name, inst.user_id, inst.user_name, inst.service,
                            "stop", "ok:auto_ttl" if ok else "error:%s" % code,
                            detail=((data.get("out") or data.get("error") or "")[:1000]
                                    if isinstance(data, dict) else None) or None)
        db.session.delete(inst)
        db.session.commit()
        reaped.append(inst.challenge_name)
    return jsonify({"success": True, "reaped": reaped, "checked": now.isoformat() + "Z"})


@bp.route("/api/lab/audit")
@admins_only
def lab_audit():
    """Historial de despliegues/tumbas. SOLO administradores."""
    q = RootPathLabAction.query
    uid = request.args.get("user_id", type=int)
    if uid:
        q = q.filter(RootPathLabAction.user_id == uid)
    act = request.args.get("action")
    if act:
        q = q.filter(RootPathLabAction.action == act)
    ch = request.args.get("challenge")
    if ch:
        q = q.filter(RootPathLabAction.challenge_name.like("%" + ch + "%"))
    res = request.args.get("result")
    if res:
        q = q.filter(RootPathLabAction.result.like(res + "%"))
    limit = min(max(request.args.get("limit", type=int) or 100, 1), 500)
    total = q.count()
    rows = q.order_by(RootPathLabAction.id.desc()).limit(limit).all()
    return jsonify({"success": True, "total": total, "count": len(rows),
                    "data": [r.as_dict() for r in rows]})


HIDE_PREFIXES = ("/challenges", "/scoreboard", "/users", "/teams", "/team/",
                 "/notifications", "/settings", "/awards", "/rules", "/register",
                 "/pages/", "/page/", "/solutions", "/hints", "/dynamic_challenges",
                 "/brackets", "/confirm", "/reset", "/edit", "/profile")
SAFE_PREFIXES = ("/api/", "/plugins/", "/themes/", "/static/", "/files/", "/admin",
                 "/login", "/logout", "/setup", "/favicon")


def _redir():
    u = get_current_user()
    return redirect("/plugins/rootpath/dashboard" if u else "/plugins/rootpath/welcome")


@bp.route("/welcome")
def welcome():
    """Landing publica: presentacion + login + registro."""
    if get_current_user():
        return redirect("/plugins/rootpath/dashboard")
    f = UserFields.query.filter_by(name="Nombre completo").first()
    return render_template("welcome.html",
                           default_tab=request.args.get("tab", "login"),
                           fullname_field_id=(f.id if f else None))


@bp.before_app_request
def _hide_ctfd():
    if request.method != "GET":
        return
    p = request.path
    if p == "/":
        return _redir()
    if p == "/login":
        return redirect("/plugins/rootpath/welcome")
    if p == "/register":
        return redirect("/plugins/rootpath/welcome?tab=register")
    if (p in ("/admin", "/admin/statistics", "/admin/scoreboard",
              "/admin/challenges", "/admin/users") or p.startswith("/admin/submissions")):
        return redirect("/plugins/rootpath/admin")
    for safe in SAFE_PREFIXES:
        if p.startswith(safe):
            return
    for pre in HIDE_PREFIXES:
        if p.startswith(pre):
            return _redir()
    # Cualquier pagina CTFd (p. ej. el panel antiguo "cyber-range") -> dashboard actual.
    route = p.strip("/")
    if route and Pages.query.filter_by(route=route).first() is not None:
        return _redir()
