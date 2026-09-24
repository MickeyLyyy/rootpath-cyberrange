import collections, time, audit, actions, config
ALLOW = {
    "monitor": {"read_metrics", "list_guests", "pool_members", "stop_guest",
                "set_deploy_paused", "write_status", "alert"},
    "curador": {"list_paths", "recommend_next", "request_deploy"},
    "tutor":   {"get_hint"},
    "creador": {"generate_challenge", "list_staging"},
    "validador": {"validate_challenge"},
    "mentor": {"approve_challenge", "reject_challenge", "publish_challenge"},
}
RATE = {"monitor": 120, "curador": 30, "tutor": 30, "creador": 30, "validador": 30, "mentor": 30}
_calls = collections.defaultdict(list)
class Denied(PermissionError):
    pass
def call(agent, action, params=None):
    params = params or {}
    now = time.time()
    _calls[agent] = [t for t in _calls[agent] if now - t < 60]
    if len(_calls[agent]) >= RATE.get(agent, 30):
        audit.write(config.AUDIT_LOG, {"agent": agent, "action": action, "params": params, "result": "denied:rate_limit"})
        raise Denied("rate limit excedido para %s" % agent)
    _calls[agent].append(now)
    if action not in ALLOW.get(agent, set()):
        audit.write(config.AUDIT_LOG, {"agent": agent, "action": action, "params": params, "result": "denied:not_allowed"})
        raise Denied("accion '%s' no permitida para el agente '%s'" % (action, agent))
    try:
        res = actions.execute(action, params)
    except Exception as e:
        audit.write(config.AUDIT_LOG, {"agent": agent, "action": action, "params": params, "result": "error:%s" % e})
        raise
    audit.write(config.AUDIT_LOG, {"agent": agent, "action": action, "params": params, "result": "ok"})
    return res
