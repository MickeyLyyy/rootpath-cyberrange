import json, hashlib, os, time, threading
_lock = threading.Lock()
def _last_hash(path):
    if not os.path.exists(path):
        return "GENESIS"
    h = "GENESIS"
    with open(path) as f:
        for line in f:
            try:
                h = json.loads(line)["hash"]
            except Exception:
                pass
    return h
def write(path, entry):
    with _lock:
        entry = dict(entry)
        entry["ts"] = time.time()
        prev = _last_hash(path)
        entry["prev"] = prev
        raw = json.dumps(entry, sort_keys=True)
        entry["hash"] = hashlib.sha256((prev + raw).encode()).hexdigest()
        with open(path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
def verify(path):
    prev = "GENESIS"
    n = 0
    with open(path) as f:
        for line in f:
            e = json.loads(line)
            stored = e.pop("hash")
            raw = json.dumps(e, sort_keys=True)
            calc = hashlib.sha256((prev + raw).encode()).hexdigest()
            if calc != stored or e["prev"] != prev:
                return False, n
            prev = stored
            n += 1
    return True, n
