import json, time, config, bus
def cycle():
    m = bus.call("monitor", "read_metrics")
    high = m["cpu_pct"] >= config.CPU_THRESHOLD or m["mem_pct"] >= config.MEM_THRESHOLD
    members = bus.call("monitor", "pool_members")
    status = {"metrics": m, "paused": high, "ts": time.time(),
              "pool": [{"vmid": x.get("vmid"), "name": x.get("name"), "status": x.get("status"),
                        "cpu": x.get("cpu"), "mem": x.get("mem")} for x in members]}
    if high:
        running = [x for x in members if x.get("status") == "running"]
        running.sort(key=lambda x: x.get("cpu") or 0, reverse=True)
        if running:
            top = running[0]
            bus.call("monitor", "stop_guest", {"vmid": top["vmid"], "type": top.get("type", "lxc")})
            bus.call("monitor", "alert", {"reason": "load_high", "stopped": top["vmid"],
                                          "cpu": top.get("cpu"), "metrics": m})
            status["action"] = "stopped_%s_y_pausado" % top["vmid"]
        else:
            bus.call("monitor", "alert", {"reason": "load_high_sin_guest_en_pool", "metrics": m})
            status["action"] = "pausado_sin_victima"
        bus.call("monitor", "set_deploy_paused", {"paused": True})
    else:
        bus.call("monitor", "set_deploy_paused", {"paused": False})
        status["action"] = "normal"
    bus.call("monitor", "write_status", {"status": status})
    return status
def main():
    import sys
    once = "--once" in sys.argv
    while True:
        try:
            print(json.dumps(cycle()))
        except Exception as e:
            print("ERROR:", e)
        if once:
            break
        time.sleep(config.INTERVAL)
if __name__ == "__main__":
    main()
