import os
NODE = "proxmox"
PVE_HOST = "172.170.10.10"
PVE_PORT = 8006
TOKENID = "rootpath-monitor@pve!monitor"
_HERE = os.path.dirname(os.path.abspath(__file__))
SECRET = open(os.path.join(_HERE, "pve_token")).read().strip()
POOL = "agentmanaged"
CPU_THRESHOLD = 60.0
MEM_THRESHOLD = 85.0
INTERVAL = 15
RUNTIME = "/opt/rootpath/runtime"
AUDIT_LOG = os.path.join(_HERE, "audit.jsonl")
CTFD_BASE = "http://127.0.0.1:8000"
