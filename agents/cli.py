import sys, json, bus, config, audit
def main():
    if len(sys.argv) < 3:
        print("uso: cli.py <agente> <accion> [json_params]")
        print("     cli.py audit tail [n] | cli.py audit verify")
        return
    a, act = sys.argv[1], sys.argv[2]
    if a == "audit":
        if act == "verify":
            ok, n = audit.verify(config.AUDIT_LOG)
            print("cadena_valida=%s entradas=%d" % (ok, n)); return
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 15
        for line in open(config.AUDIT_LOG).read().splitlines()[-n:]:
            e = json.loads(line)
            print("%.0f %-8s %-18s %s" % (e["ts"], e["agent"], e["action"], e["result"]))
        return
    params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    try:
        print(json.dumps(bus.call(a, act, params), indent=2))
    except Exception as e:
        print("DENIED/ERROR:", e)
if __name__ == "__main__":
    main()
