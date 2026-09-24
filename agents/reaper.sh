#!/bin/bash
KEY=$(cat /opt/rootpath/runtime/agent_key 2>/dev/null)
[ -z "$KEY" ] && exit 0
curl -s -m 25 -H "X-Agent-Key: $KEY" http://127.0.0.1:8000/plugins/rootpath/api/agent/reap >/dev/null 2>&1
