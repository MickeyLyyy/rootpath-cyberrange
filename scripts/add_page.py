import requests
TOK = open('/opt/rootpath/.admin_token').read().strip()
H = {"Authorization": "Token " + TOK, "Content-Type": "application/json"}
content = open('/opt/rootpath/docs/writeups/TEMPLATE.md').read()
r = requests.post("http://127.0.0.1:8000/api/v1/pages", headers=H,
    json={"title": "Plantilla de Writeups", "route": "writeup-template",
          "content": content, "format": "markdown", "draft": False})
print("page:", r.status_code, r.text[:150])
