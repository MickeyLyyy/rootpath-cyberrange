from flask import Flask, request
import subprocess
app = Flask(__name__)

@app.route("/")
def ping():
    host = request.args.get("host", "127.0.0.1")
    res = subprocess.run("ping -c 1 " + host, shell=True, capture_output=True, text=True)
    return "<h1>Ping</h1><pre>" + res.stdout + res.stderr + "</pre>"

app.run(host="0.0.0.0", port=5000)
